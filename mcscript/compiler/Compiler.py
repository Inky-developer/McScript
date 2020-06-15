from typing import Dict, List, Tuple

from lark import Token, Tree
from lark.visitors import Interpreter

from mcscript import Logger
from mcscript.analyzer.Analyzer import NamespaceContext
from mcscript.compiler.common import conditional_loop, get_property, readContextManipulator, set_property
from mcscript.compiler.CompileState import CompileState
from mcscript.compiler.ContextType import ContextType
from mcscript.compiler.tokenConverter import convertToken
from mcscript.data import defaultCode
from mcscript.data.commands import BinaryOperator, Command, ExecuteCommand, multiple_commands, Relation, UnaryOperator
from mcscript.data.Config import Config
from mcscript.exceptions.compileExceptions import (
    McScriptArgumentsError,
    McScriptChangedTypeError, McScriptDeclarationError,
    McScriptIsStaticError, McScriptNameError,
    McScriptNotStaticError, McScriptSyntaxError, McScriptTypeError,
)
from mcscript.lang.builtins.builtins import BuiltinFunction
from mcscript.lang.resource.base.FunctionResource import Parameter
from mcscript.lang.resource.base.ResourceBase import ObjectResource, Resource, ValueResource
from mcscript.lang.resource.BooleanResource import BooleanResource
from mcscript.lang.resource.DefaultFunctionResource import DefaultFunctionResource
from mcscript.lang.resource.EnumResource import EnumResource
from mcscript.lang.resource.InlineFunctionResource import InlineFunctionResource
from mcscript.lang.resource.NbtAddressResource import NbtAddressResource
from mcscript.lang.resource.NullResource import NullResource
from mcscript.lang.resource.StructMethodResource import StructMethodResource
from mcscript.lang.resource.StructResource import StructResource
from mcscript.lang.resource.TupleResource import TupleResource
from mcscript.lang.resource.TypeResource import TypeResource
from mcscript.lang.utility import compareTypes, isStatic
from mcscript.utils.Datapack import Datapack


class Compiler(Interpreter):
    def __init__(self):
        # noinspection PyTypeChecker
        self.compileState: CompileState = None

    def visit(self, tree):
        previous = self.compileState.currentTree
        try:
            self.compileState.currentTree = tree
        except AttributeError:
            raise ValueError("Cannot visit without a compile state. Use ´compile´ instead.")

        result = super().visit(tree)
        self.compileState.currentTree = previous
        return result

    def compile(self, tree: Tree, contexts: Dict[Tuple[int, int], NamespaceContext], code: str,
                config: Config) -> Datapack:
        self.compileState = CompileState(code, contexts, self.visit, config)
        self.compileState.fileStructure.pushFile("main.mcfunction")
        BuiltinFunction.load(self)
        self.compileState.pushContext(ContextType.GLOBAL, 0, 0)
        self.visit(tree)

        # ToDO put this in default code
        # create file with all constants
        self.compileState.fileStructure.pushFile("init_constants.mcfunction")
        self.compileState.compilerConstants.write_constants(self.compileState)

        self.compileState.fileStructure.pushFile("init_scoreboards.mcfunction")
        for scoreboard in self.compileState.scoreboards:
            scoreboard.writeInit(self.compileState.fileStructure)

        return self.compileState.datapack

    #  called by every registered builtin function
    def loadFunction(self, function: BuiltinFunction):
        # ToDo: Make BuiltinFunction officially a resource
        # noinspection PyTypeChecker
        self.compileState.currentContext().add_var(function.name(), function)

    #######################
    #    tree handlers    #
    #######################
    def boolean_constant(self, tree):
        return BooleanResource(tree.children[0] == "True", True)

    def value(self, tree):
        """ a value is a simple token or expression that can be converted to a resource"""
        value = tree.children[0]

        if isinstance(value, Tree):
            ret = self.visit(value)
            return ret
        elif isinstance(value, Token):
            return convertToken(value, self.compileState)
        raise McScriptNameError(f"Invalid value: {value}", self.compileState)

    def tuple(self, tree):
        elements = [self.visit(i) for i in tree.children]
        return TupleResource(*elements)

    # enums
    def control_enum(self, tree):
        _, name, block = tree.children
        properties, value_properties = self.visit(block)

        try:
            enum = EnumResource(*properties, **value_properties)
        except ValueError as e:
            raise McScriptDeclarationError(e.args[0], self.compileState)
        except TypeError as e:
            raise McScriptTypeError(e.args[0], self.compileState)

        self.compileState.currentContext().add_var(name, enum)

    def enum_block(self, tree):
        properties = []
        value_properties = {}

        for child in tree.children:
            name, *value = self.visit(child)

            if name in properties:
                raise McScriptNameError(f"Enum member {name} was already defined for this enum", self.compileState)
            if value:
                value_properties[name] = value[0]
            else:
                properties.append(name)

        return properties, value_properties

    def enum_property(self, tree):
        identifier, *value = tree.children
        if value:
            return identifier, convertToken(value[0], self.compileState)
        return identifier,

    def accessor(self, tree):
        """
        a variable or a list of dot separated names like a.b.c will be loaded here.
        """
        accessed = get_property(self.compileState, tree)
        return accessed[-1]

    def array_accessor(self, tree):
        """ Accesses an element on an array"""
        accessor_, index_ = tree.children

        accessor = self.visit(accessor_)
        index = self.compileState.toResource(index_)

        try:
            self.compileState.currentTree = index_
            return accessor.operation_get_element(self.compileState, index)
        except TypeError:
            raise McScriptTypeError(f"{accessor.type().value} does not support reading index access", self.compileState)

    def index_setter(self, tree):
        accessor, index, value = tree.children

        accessor = self.visit(accessor)
        index = self.compileState.toResource(index)
        value = self.compileState.toResource(value)

        try:
            return accessor.operation_set_element(self.compileState, index, value)
        except TypeError:
            raise McScriptTypeError(f"{accessor.type().value} does not support writing index access", self.compileState)

    def propertySetter(self, tree):
        identifier, value = tree.children
        value = self.compileState.toResource(value)
        set_property(self.compileState, identifier, value)
        return value

    def unary_operation(self, tree):
        # noinspection PyShadowingNames
        def doOperation(operator: UnaryOperator, value: Resource):
            if operator == UnaryOperator.MINUS:
                return value.operation_negate(self.compileState)
            elif operator == UnaryOperator.DECREMENT_ONE:
                return value.operation_decrement_one(self.compileState)
            elif operator == UnaryOperator.INCREMENT_ONE:
                return value.operation_increment_one(self.compileState)
            raise ValueError(f"Unknown unary operator {operator.name} in unary_operation")

        operator, value = tree.children
        value = self.compileState.toResource(value)
        operator = UnaryOperator(operator)

        # first try to do the operation on the resource itself.
        # if that is not possible, load the resource and try again
        try:
            return doOperation(operator, value)
        except TypeError:
            value = value.load(self.compileState)
            try:
                return doOperation(operator, value)
            except TypeError:
                raise McScriptTypeError(f"Could not perform operation {operator.name} on {repr(value)}",
                                        self.compileState)

    def boolean_and(self, tree):
        rest = tree.children

        _conditions = [rest[0]]
        rest = rest[1:]
        while rest:
            _, a, *rest = rest
            _conditions.append(a)

        conditions = []
        for condition in _conditions:
            condition = self.compileState.load(condition).convertToBoolean(self.compileState)
            if condition.isStatic:
                if condition.value:
                    continue
                Logger.warn(f"[Compiler] boolean and at {tree.line}:{tree.column} is always False.")
                return BooleanResource.FALSE
            conditions.append(condition)

        if not conditions:
            Logger.warning(f"[Compiler] boolean and {tree.line}:{tree.column} is always True.")
            return BooleanResource.TRUE

        stack = self.compileState.expressionStack.next()

        previous = ""
        for condition in conditions:
            previous = ExecuteCommand.IF_SCORE_RANGE(
                stack=condition.value,
                range=1,
                command=previous
            )
        command = Command.EXECUTE(
            sub=previous,
            command=Command.SET_VALUE(
                stack=stack,
                value=1
            )
        )

        self.compileState.writeline(multiple_commands(
            Command.SET_VALUE(stack=stack, value=0),
            command
        ))
        return BooleanResource(stack, False)

    def boolean_or(self, tree):
        rest = tree.children

        _conditions = [rest[0]]
        rest = rest[1:]
        while rest:
            _, a, *rest = rest
            _conditions.append(a)
        conditions = []

        for condition in _conditions:
            value = self.compileState.toResource(condition).convertToBoolean(self.compileState)
            if value.isStatic:
                if value.value:
                    Logger.debug(f"[Compiler] boolean or is always True at line {tree.line} column {tree.column}")
                    return BooleanResource.TRUE
                # always False boolean does not matter, so it will be discarded
                continue

            conditions.append(value)

        if not conditions:
            Logger.debug(f"[Compiler] boolean or is always False at {tree.line} column {tree.column} ")
            return BooleanResource.FALSE

        stack = self.compileState.expressionStack.next()

        commands = []
        for condition in conditions:
            commands.append(Command.EXECUTE(
                sub=ExecuteCommand.IF_SCORE_RANGE(
                    stack=condition,
                    range=1
                ),
                command=Command.SET_VALUE(
                    stack=stack,
                    value=1
                )
            ))

        if commands:
            self.compileState.writeline(multiple_commands(
                Command.SET_VALUE(stack=stack, value=0),
                *commands
            ))
            return BooleanResource(stack, False)

    def boolean_not(self, tree):
        _, value = tree.children
        value = self.compileState.toResource(value).convertToBoolean(self.compileState)
        if value.isStatic:
            return BooleanResource(not value.value, True)

        stack = self.compileState.expressionStack.next()
        self.compileState.writeline(Command.SET_VALUE(
            stack=stack,
            value=0
        ))
        self.compileState.writeline(Command.EXECUTE(
            sub=ExecuteCommand.IF_SCORE_RANGE(
                stack=value.value,
                range=0
            ),
            command=Command.SET_VALUE(
                stack=stack,
                value=1
            )
        ))

        return BooleanResource(stack, False)

    def binaryOperation(self, *args):
        number1, *values = args

        # the first number can also be a list. Then just do a binary operation with it
        if isinstance(number1, list):
            number1 = self.binaryOperation(*number1)
        number1 = self.compileState.load(number1)
        for i in range(0, len(values), 2):
            operator, number2, = values[i:i + 2]
            if isinstance(number2, list):
                number2 = self.binaryOperation(*number2)

            # get the operator enum type
            operator = BinaryOperator(operator)

            number2 = self.compileState.load(number2)

            try:
                result = number1.numericOperation(number2, operator, self.compileState)
                if result == NotImplemented:
                    raise McScriptTypeError(f"Operation <{operator.name}> not supported between operands "
                                            f"'{number1.type().value}' and '{number2.type().value}'", self.compileState)
                number1 = result
            except NotImplementedError:
                raise TypeError(f"Expected operand that supports numeric operations, not {repr(number1)}")
        return number1

    def term(self, tree):
        term = tree.children[0]
        if term.data in ("sum", "product"):  # this term does not contain operands
            return self.binaryOperation(*self.visit_children(tree.children[0]))
        return self.visit(term)

    def comparison(self, tree):
        left, operator, right = tree.children
        left = self.compileState.toResource(left)
        right = self.compileState.toResource(right)
        operator = Relation.get(operator.type)

        try:
            # if this operation goes wrong, the contextmanager discards all writes
            with self.compileState.push():
                relation = left.operation_test_relation(self.compileState, operator, right)
                self.compileState.commit()
        except TypeError:
            # if this operation is not possible, try the other way around
            try:
                relation = right.operation_test_relation(self.compileState, operator.swap(), left)
            except TypeError:
                raise McScriptTypeError(f"Comparison not available for {left.type().value} "
                                        f"and {right.type().value}", self.compileState)

        return relation

    def _set_variable(self, identifier: str, value: Resource, force_new_stack=True):
        """
        Sets a variable in the current namespace.

        Args:
            identifier: the name of the variable
            value: the value of the variable
            force_new_stack: Whether a new stack is required. If False the value might simply get copied.
        """
        if identifier in self.compileState.currentContext():
            set_method = self.compileState.currentContext().set_var
            variable = self.compileState.currentContext().find_var(identifier)
            stack = variable.resource

            if not compareTypes(value, stack):
                raise McScriptChangedTypeError(identifier, value, self.compileState)

            if isStatic(stack):
                variable_data = variable.context

                if not isStatic(value):
                    raise McScriptIsStaticError(
                        "Trying to assign non-static value to static variable",
                        variable_data.declaration.access,
                        self.compileState
                    )

                non_static_context = self.compileState.currentContext().search_non_static_until(
                    self.compileState.stack.search_by_pos(*variable_data.declaration.master_context)
                )

                if non_static_context is not None:
                    raise McScriptIsStaticError(
                        f"Trying to change the value here\nIn between is a non-static namespace "
                        f"{non_static_context.context_type.name} (ToDo show line for this)",
                        variable_data.declaration.access,
                        self.compileState,
                    )

            if isinstance(stack, ValueResource) and isinstance(stack.value, NbtAddressResource):
                stack = stack.value
            elif isinstance(stack, ObjectResource):
                try:
                    stack = stack.getBasePath()
                except TypeError:
                    stack = self.compileState.currentContext().nbt_format.with_name(identifier)
            else:
                stack = self.compileState.currentContext().nbt_format.with_name(identifier)

            # what is this bs?
            # # Redefining a variable can lead to errors.
            # # for example, consider: a="Test"; fun onTick() { a = a + "|" }
            # # this code would only add one | to the string instead of one every tick. This is because a string
            # # needs a static context to do this operation
            # # (static context := known at compile time how often this code will run)
            # # For this reason we have to "ask" the resource if redefining it in the current context is ok.
            # if not value.allow_redefine(self.compileState):
            #     scope = "static" if self.compileState.currentNamespace().isContextStatic() else "non-static"
            #     # ToDo better error message (which provides help)
            #     raise McScriptDeclarationError(
            #        f"Trying to redefine a variable of type {value.type().value} in a {scope} scope", self.compileState
            #     )
        else:
            # create a new stack value
            stack = self.compileState.currentContext().nbt_format.with_name(identifier)
            set_method = self.compileState.currentContext().add_var

        try:
            # var = value.load(self.compileState).storeToNbt(stack, self.compileState)
            var = value.storeToNbt(stack, self.compileState) if force_new_stack else value
        except TypeError:
            var = value
            # The null resource is kinda special because it only ever has one value
            if not isinstance(value, NullResource):
                raise McScriptTypeError(f"Could not assign type {value.type().value} to a variable because "
                                        f"it does not support this operation", self.compileState)

        set_method(identifier, var)
        return var

    def declaration(self, tree):
        identifier, _value = tree.children
        if len(identifier.children) != 1:
            return self.propertySetter(tree)

        identifier, = identifier.children

        value = self.compileState.toResource(_value)
        force_stack = identifier not in self.compileState.currentContext() or not isStatic(
            self.compileState.currentContext().find_resource(identifier))

        self.compileState.currentTree = _value
        self._set_variable(identifier, value, force_stack)

    def multi_declaration(self, tree):
        *variables, expression = tree.children
        expression = self.compileState.toResource(expression)

        if not isinstance(expression, TupleResource):
            raise McScriptTypeError(
                f"Return type deconstruction works only for arrays, but not for type {expression.type().value}",
                self.compileState
            )

        if (size := expression.getAttribute(self.compileState, "size").toNumber()) != len(variables):
            raise McScriptDeclarationError(
                f"Array must contain exactly {len(variables)} elements but found {size}:\n"
                f'({", ".join(i.type().value for i in expression.resources)})',
                self.compileState
            )

        for variable, value in zip(variables, expression.resources):
            variable, = variable.children
            self._set_variable(variable, value, False)

    def static_declaration(self, tree):
        declaration = tree.children[0]
        identifier, value = declaration.children
        if len(identifier.children) > 1:
            raise McScriptSyntaxError(f"Cannot set a static value on an object.", self.compileState)
        identifier, = identifier.children
        value = self.compileState.toResource(value)

        if isinstance(value, ObjectResource):
            raise McScriptTypeError(f"Only simple datatypes can be assigned using static, not {value.type().value}",
                                    self.compileState)

        if isinstance(value, ValueResource) and not value.hasStaticValue:
            raise McScriptNotStaticError("static declaration needs a static value", self.compileState)

        self.compileState.currentContext().add_var(identifier, value)

    def term_ip(self, tree):
        """
        calculates the result of the expression and stores the result back into the variable

        trees: variable, operator, resource

        1. Get the variable
        2. calculate the expression
        3. store the result back into the variable
            a. if the variable is not a property, just use set_var
            b. if the variable is a property, use set_property
        """
        accessor, operator, expression = tree.children

        resource = self.compileState.toResource(accessor)
        expression = self.compileState.toResource(expression)

        if not isinstance(expression, ValueResource):
            raise McScriptTypeError(f"in-place operation: Expected value, got {expression}", self.compileState)

        # do the numeric operation
        result = resource.load(self.compileState).numericOperation(
            expression,
            BinaryOperator(operator),
            self.compileState
        )

        # store the result back
        set_property(self.compileState, accessor, result)

    def block(self, tree: Tree):
        blockName = self.compileState.pushBlock(ContextType.BLOCK, tree.line, tree.column)
        newNamespace = self.compileState.currentContext()
        self.visit_children(tree)
        self.compileState.popBlock()
        return blockName, newNamespace

    def control_if(self, tree):
        condition, block, block_else = tree.children

        if not block.children:
            Logger.debug(f"[Compiler] skipping if-statement line {tree.line}: empty block")
            return None

        condition = self.compileState.toCondition(condition)
        if condition.isStatic:
            # if the result is already known execute either the if or else block
            if condition.condition is True:
                self.visit_children(block)
                Logger.debug(f"If statement at line {tree.line} column {tree.column} is always True")
            elif block_else is not None:
                self.visit_children(block_else)
                Logger.debug(f"If statement at line {tree.line} column {tree.column} is always False")
            return

        blockName = self.compileState.pushBlock(ContextType.CONDITIONAL, block.line, block.column)
        self.visit_children(block)
        self.compileState.popBlock()

        if block_else is not None:
            cond_if, cond_else = condition.if_else(self.compileState)

            blockElseName = self.compileState.pushBlock(ContextType.CONDITIONAL, block_else.line, block_else.column)
            self.visit_children(block_else)
            self.compileState.popBlock()

            self.compileState.writeline(cond_if(Command.RUN_FUNCTION(function=blockName)))
            self.compileState.writeline(cond_else(Command.RUN_FUNCTION(function=blockElseName)))
        else:
            self.compileState.writeline(condition(Command.RUN_FUNCTION(function=blockName)))

    def control_do_while(self, tree):
        context, block, _condition = tree.children
        return conditional_loop(self.compileState, block, _condition, False, context)

    def control_while(self, tree):
        _condition, context, block = tree.children
        return conditional_loop(self.compileState, block, _condition, True, context)

    def control_for(self, tree):
        _, var_name, _, expression, block = tree.children

        resource = self.compileState.toResource(expression)
        try:
            resource.iterate(self.compileState, var_name, block)
        except TypeError:
            raise McScriptTypeError(f"type {resource.type().value} does not support iteration", self.compileState)

    def return_(self, tree):
        resource = self.compileState.toResource(tree.children[0])
        if self.compileState.currentContext().return_resource is not None:
            raise McScriptSyntaxError("Cannot set the return value twice.", self.compileState)
        self.compileState.currentContext().return_resource = resource

    def function_parameter(self, tree):
        identifier, datatype = tree.children
        datatype = convertToken(datatype, self.compileState)
        return identifier, TypeResource(datatype, True)

    def function_definition(self, tree):
        inline, _, function_name, parameter_list, return_type, block = tree.children
        # a function will be inlined if so specified or if it is declared in a struct scope.
        isMethod = self.compileState.currentContext().context_type == ContextType.STRUCT
        inline = inline or isMethod
        parameter_list = [self.visit(i) for i in parameter_list.children]

        # the return type can be omitted. In this case, it will be Null
        return_type = TypeResource(
            convertToken(return_type, self.compileState) if return_type else NullResource,
            True
        )

        if (any(parameter.value.requiresInlineFunc for _, parameter in
                parameter_list) or return_type.value.requiresInlineFunc) and not inline:
            raise McScriptTypeError(f"Some parameters (or the return type) can only be used in an inline context. "
                                    f"Consider declaring this function using 'inline fun'.", self.compileState)

        if not inline:
            return self.function_definition_normal(function_name, parameter_list, return_type, block)

        return self.function_definition_inline(function_name, parameter_list, return_type, block, isMethod)

    def function_definition_inline(self, function_name: str, parameter_list: List[Parameter], return_type: TypeResource,
                                   block: Tree, isMethod: bool):
        if function_name in defaultCode.MAGIC_FUNCTIONS:
            raise McScriptSyntaxError("Special functions must not be inlined", self.compileState)

        FunctionCls = StructMethodResource if isMethod else InlineFunctionResource

        function = FunctionCls(function_name, parameter_list, return_type, block)
        self.compileState.currentContext().add_var(function.name(), function)

    def function_definition_normal(self, function_name: str, parameter_list: List[Parameter], return_type: TypeResource,
                                   block: Tree):
        function = DefaultFunctionResource(function_name, parameter_list, return_type, block)
        function.compile(self.compileState)
        self.compileState.currentContext().add_var(function.name(), function)

        is_special = function_name in defaultCode.MAGIC_FUNCTIONS
        if is_special:
            param_count = defaultCode.MAGIC_FUNCTIONS[function_name]
            if param_count != len(function.parameters):
                raise McScriptArgumentsError(
                    f"Magic method {function.name()} must accept exactly {param_count} parameters",
                    self.compileState
                )
            self.compileState.fileStructure.setPoi(function)

    def builtinFunction(self, function: BuiltinFunction, *parameters: Resource):
        loadFunction = self.compileState.load if not function.requireRawParameters() else self.compileState.toResource
        # noinspection PyArgumentList
        parameters = [loadFunction(i) for i in parameters]

        result = function.create(self.compileState, *parameters)
        if result.code:
            if result.inline:
                self.compileState.writeline(result.code)
            else:
                addr = self.compileState.fileStructure.pushFile(self.compileState.codeBlockStack.next())
                self.compileState.writeline(result.code)
                self.compileState.fileStructure.popFile()

                self.compileState.writeline(Command.RUN_FUNCTION(function=addr))

        return result.resource

    def function_call(self, tree):
        function_name, *parameters = tree.children
        *accessed_objects, function = get_property(self.compileState, function_name)
        if isinstance(function, BuiltinFunction):
            return self.builtinFunction(function, *parameters)

        visited_params = [self.visit(i) for i in parameters]

        # a method will get the object as an argument
        if isinstance(function, StructMethodResource):
            return function.operation_call(self.compileState, accessed_objects[-1], *visited_params)
        # any object that implements the call operator can be called. This of course includes function resources.
        try:
            return function.operation_call(self.compileState, *visited_params)
        except TypeError:
            raise McScriptTypeError(f"The resource {repr(function)} can not be treated like a function",
                                    self.compileState)

    def variable_declaration(self, tree):
        identifier, datatype = tree.children
        self.compileState.currentContext().add_var(identifier, TypeResource(
            convertToken(datatype, self.compileState), True
        ))

    def control_struct(self, tree):
        name, block = tree.children
        self.compileState.pushContext(ContextType.STRUCT, block.line, block.column)
        context = self.compileState.currentContext()

        struct = StructResource(name, context)

        # this is not nice, but the struct must be referencable within itself
        self.compileState.currentContext().add_var(name, struct)

        for declaration in block.children:
            self.visit(declaration)
        self.compileState.popContext()
        self.compileState.currentContext().add_var(name, struct)

    def context_manipulator(self, tree: Tree):
        *modifiers, block = tree.children

        blockName = self.compileState.pushBlock(ContextType.CONTEXT_MANIPULATOR, block.line, block.column)
        self.visit_children(block)
        self.compileState.popBlock()

        self.compileState.writeline(Command.EXECUTE(
            sub=readContextManipulator(modifiers, self.compileState),
            command=Command.RUN_FUNCTION(
                function=blockName
            )
        ))

    def expression(self, tree):
        return self.visit(tree.children[0])

    def statement(self, tree):
        self.compileState.writeline(f"# {self.compileState.getDebugLines(tree.meta.line, tree.meta.end_line)}")
        res = self.visit_children(tree)
        # # now clear up the expression counter
        self.compileState.expressionStack.reset()
        self.compileState.temporaryStorageStack.reset()
        # for readability
        self.compileState.writeline()
        return res
