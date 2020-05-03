from typing import List

from lark import Token, Tree
from lark.visitors import Interpreter

from mcscript import Logger
from mcscript.Exceptions.compileExceptions import McScriptArgumentsError, McScriptChangedTypeError, \
    McScriptDeclarationError, \
    McScriptIsStaticError, McScriptNameError, \
    McScriptNotStaticError, McScriptSyntaxError, McScriptTypeError
from mcscript.Exceptions.utils import requireType
from mcscript.analyzer.Analyzer import NamespaceContext
from mcscript.compiler.CompileState import CompileState
from mcscript.compiler.NamespaceType import NamespaceType
from mcscript.compiler.tokenConverter import convertToken
from mcscript.data import defaultCode, defaultEnums
from mcscript.data.Config import Config
from mcscript.data.commands import BinaryOperator, Command, ConditionalExecute, ExecuteCommand, Relation, UnaryOperator, \
    multiple_commands
from mcscript.lang.builtins.builtins import BuiltinFunction
from mcscript.lang.resource.ArrayResource import ArrayResource
from mcscript.lang.resource.BooleanResource import BooleanResource
from mcscript.lang.resource.DefaultFunctionResource import DefaultFunctionResource
from mcscript.lang.resource.EnumResource import EnumResource
from mcscript.lang.resource.InlineFunctionResource import InlineFunctionResource
from mcscript.lang.resource.NbtAddressResource import NbtAddressResource
from mcscript.lang.resource.NullResource import NullResource
from mcscript.lang.resource.SelectorResource import SelectorResource
from mcscript.lang.resource.StructMethodResource import StructMethodResource
from mcscript.lang.resource.StructResource import StructResource
from mcscript.lang.resource.TypeResource import TypeResource
from mcscript.lang.resource.base.FunctionResource import Parameter
from mcscript.lang.resource.base.ResourceBase import ObjectResource, Resource, ValueResource
from mcscript.lang.utility import compareTypes
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

    def compile(self, tree: Tree, contexts: List[NamespaceContext], code: str, config: Config) -> Datapack:
        self.compileState = CompileState(code, contexts, self.visit, config)
        self.compileState.fileStructure.pushFile("main.mcfunction")
        BuiltinFunction.load(self)
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
        self.compileState.currentNamespace().addFunction(function)

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
            if value.data == "accessor":
                return ret[-1]
            return ret
        elif isinstance(value, Token):
            return convertToken(value, self.compileState)
        raise McScriptNameError(f"Invalid value: {value}", self.compileState)

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

        self.compileState.currentNamespace()[name] = enum

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

        Returns:
            a list of all objects that were accessed
        """
        ret, *values = tree.children
        if ret not in self.compileState.currentNamespace():
            if result := defaultEnums.get(ret):
                self.compileState.stack.stack[0][ret] = result
            else:
                raise McScriptNameError(f"Unknown variable '{ret}'", self.compileState)

        accessed = [self.compileState.currentNamespace()[ret]]
        for value in values:
            try:
                accessed.append(accessed[-1].getAttribute(self.compileState, value))
            except TypeError:
                raise McScriptTypeError(f"Cannot access property '{value}' of {accessed[-1].type().value}",
                                        self.compileState)
        return accessed

    def array_accessor(self, tree):
        """ Accesses an element on an array"""
        accessor_, index_ = tree.children

        accessor, = self.visit(accessor_)
        index = self.compileState.toResource(index_)

        try:
            self.compileState.currentTree = index_
            return accessor.operation_get_element(self.compileState, index)
        except TypeError:
            raise McScriptTypeError(f"{accessor.type().value} does not support reading index access", self.compileState)

    def index_setter(self, tree):
        accessor, index, value = tree.children

        accessor, = self.visit(accessor)
        index = self.compileState.toResource(index)
        value = self.compileState.toResource(value)

        try:
            return accessor.operation_set_element(self.compileState, index, value)
        except TypeError:
            raise McScriptTypeError(f"{accessor.type().value} does not support writing index access", self.compileState)

    def propertySetter(self, tree):
        identifier, value = tree.children
        obj, *rest = identifier.children

        self.compileState.currentTree = obj  # manual setting because this method is called manually
        if obj not in self.compileState.currentNamespace():
            raise McScriptNameError(f"Unknown variable '{obj}'", self.compileState)
        obj = self.compileState.currentNamespace()[obj]

        for i in rest[:-1]:
            self.compileState.currentTree = i
            if not isinstance(obj, ObjectResource):
                raise McScriptTypeError(f"resource {obj} must be an object!", self.compileState)

            try:
                obj = obj.getAttribute(i)
            except AttributeError:
                raise McScriptNameError(f"property {i} of {obj} does not exist!", self.compileState)

        attribute = rest[-1]
        if not isinstance(obj, ObjectResource):
            raise McScriptTypeError(f"resource {obj} must be an object!", self.compileState)

        value = self.compileState.load(value)
        self.compileState.currentTree = rest[-1]
        obj.setAttribute(self.compileState, attribute, value)
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
        if identifier in self.compileState.currentNamespace():
            stack = self.compileState.currentNamespace()[identifier]

            if not compareTypes(value, stack):
                raise McScriptChangedTypeError(identifier, value, self.compileState)

            if isinstance(stack, ValueResource) and isinstance(stack.value, NbtAddressResource):
                stack = stack.value
            elif isinstance(stack, ObjectResource):
                try:
                    stack = stack.getBasePath()
                except TypeError:
                    stack = NbtAddressResource(self.compileState.currentNamespace().variableFmt.format(identifier))
            else:
                stack = NbtAddressResource(self.compileState.currentNamespace().variableFmt.format(identifier))

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
            stack = NbtAddressResource(self.compileState.currentNamespace().variableFmt.format(identifier))
        try:
            # var = value.load(self.compileState).storeToNbt(stack, self.compileState)
            var = value.storeToNbt(stack, self.compileState) if force_new_stack else value
        except TypeError as e:
            var = value
            # The null resource is kinda special because it only ever has one value
            if not isinstance(value, NullResource):
                raise McScriptTypeError(f"Could not assign type {value.type().value} to a variable because "
                                        f"it does not support this operation", self.compileState)
        self.compileState.currentNamespace().setVar(identifier, var)
        return var

    def declaration(self, tree):
        identifier, value = tree.children
        if len(identifier.children) != 1:
            return self.propertySetter(tree)
        identifier, = identifier.children
        value = self.compileState.toResource(value)
        self._set_variable(identifier, value)

    def multi_declaration(self, tree):
        *variables, expression = tree.children
        expression = self.compileState.toResource(expression)

        if not isinstance(expression, ArrayResource):
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

        if not isinstance(value, ValueResource):
            raise McScriptTypeError(f"Only simple datatypes can be assigned using const, not {value.type().value}",
                                    self.compileState)
        if not value.hasStaticValue:
            raise McScriptNotStaticError("static declaration needs a static value.", self.compileState)

        self.compileState.currentNamespace()[identifier] = value

    def term_ip(self, tree):
        variable, operator, resource = tree.children
        resource = self.compileState.load(resource)
        *_, varResource = self.visit(variable)
        var = varResource.load(self.compileState)
        if var.isStatic:
            raise McScriptIsStaticError("Cannot modify a static variable", self.compileState)
        if not isinstance(resource, ValueResource):
            raise AttributeError(f"Cannot do an operation with '{resource}'", self.compileState)

        try:
            result = var.numericOperation(resource, BinaryOperator(operator), self.compileState)
            if result == NotImplemented:
                raise McScriptTypeError(
                    f"Unsupported operation {operator} for {var.type().value} and {resource.type().value}",
                    self.compileState
                )
        except NotImplementedError:
            raise McScriptTypeError(
                f"in place operation: Failed because {repr(var)} does not support the operation {operator.name}",
                self.compileState
            )

        if not isinstance(result, Resource):
            raise McScriptTypeError(f"Expected a resource, got {result}", self.compileState)
        result.storeToNbt(varResource.value, self.compileState)

    def block(self, tree):
        blockName = self.compileState.pushBlock()
        newNamespace = self.compileState.currentNamespace()
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

        blockName = self.compileState.pushBlock(namespaceType=NamespaceType.CONDITIONAL)
        self.visit_children(block)
        self.compileState.popBlock()

        if block_else is not None:
            cond_if, cond_else = condition.if_else(self.compileState)

            blockElseName = self.compileState.pushBlock(namespaceType=NamespaceType.CONDITIONAL)
            self.visit_children(block_else)
            self.compileState.popBlock()

            self.compileState.writeline(cond_if(Command.RUN_FUNCTION(function=blockName)))
            self.compileState.writeline(cond_else(Command.RUN_FUNCTION(function=blockElseName)))
        else:
            self.compileState.writeline(condition(Command.RUN_FUNCTION(function=blockName)))

    def _conditional_loop(self, block: Tree, conditionTree: Tree, check_start: bool):
        blockName = self.compileState.pushBlock(namespaceType=NamespaceType.LOOP)
        self.visit_children(block)

        condition = self.compileState.toCondition(conditionTree)
        if condition.isStatic:
            if condition.condition:
                Logger.info(f"[Compiler] Loop at line {conditionTree.line} column {conditionTree.column} runs forever!")
            else:
                Logger.info(
                    f"[Compiler] Loop at line {conditionTree.line} column {conditionTree.column} only runs once!"
                )

        self.compileState.writeline(condition(Command.RUN_FUNCTION(function=blockName)))
        self.compileState.popBlock()

        condition = self.compileState.toCondition(conditionTree) if check_start else ConditionalExecute(True)
        self.compileState.writeline(condition(Command.RUN_FUNCTION(function=blockName)))

    def control_do_while(self, tree):
        block, _condition = tree.children
        return self._conditional_loop(block, _condition, False)

    def control_while(self, tree):
        _condition, block = tree.children
        return self._conditional_loop(block, _condition, True)

    def control_for(self, tree):
        _, var_name, _, expression, block = tree.children

        resource = self.compileState.toResource(expression)
        try:
            resource.iterate(self.compileState, var_name, block)
        except TypeError:
            raise McScriptTypeError(f"type {resource.type().value} does not support iteration", self.compileState)

    def return_(self, tree):
        resource = self.compileState.toResource(tree.children[0])
        if not isinstance(self.compileState.currentNamespace().returnedResource, NullResource):
            raise McScriptSyntaxError("Cannot set the return value twice.", self.compileState)
        self.compileState.currentNamespace().returnedResource = resource

    def function_parameter(self, tree):
        identifier, datatype = tree.children
        datatype = convertToken(datatype, self.compileState)
        return identifier, TypeResource(datatype, True)

    def function_definition(self, tree):
        inline, _, function_name, parameter_list, return_type, block = tree.children
        # a function will be inlined if so specified or if it is declared in a struct scope.
        isMethod = self.compileState.currentNamespace().namespaceType == NamespaceType.STRUCT
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
        self.compileState.currentNamespace().addFunction(function)

    def function_definition_normal(self, function_name: str, parameter_list: List[Parameter], return_type: TypeResource,
                                   block: Tree):
        function = DefaultFunctionResource(function_name, parameter_list, return_type, block)
        function.compile(self.compileState)
        self.compileState.currentNamespace().addFunction(function)

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
        parameters = [loadFunction(i) for i in parameters]

        result = function.create(self.compileState, *parameters)
        if result.code:
            if result.inline:
                self.compileState.writeline(result.code)
            else:
                addr = self.compileState.pushBlock()
                self.compileState.writeline(result.code)
                self.compileState.popBlock()
                self.compileState.writeline(Command.RUN_FUNCTION(function=addr))

        return result.resource

    def function_call(self, tree):
        function_name, *parameters = tree.children
        *accessed_objects, function = self.visit(function_name)
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
        self.compileState.currentNamespace()[identifier] = TypeResource(
            convertToken(datatype, self.compileState), True
        )

    def control_struct(self, tree):
        name, block = tree.children
        self.compileState.pushStack(NamespaceType.STRUCT)
        namespace = self.compileState.currentNamespace()

        struct = StructResource(name, namespace)

        # this is not nice, but the struct must be referencable within itself
        self.compileState.currentNamespace().setVar(name, struct)

        for declaration in block.children:
            self.visit(declaration)
        self.compileState.popStack()
        self.compileState.currentNamespace().setVar(name, struct)

    def context_manipulator(self, tree):
        def for_(selector):
            requireType(selector, SelectorResource, self.compileState)
            return ExecuteCommand.AS(target=selector)

        def at(selector):
            requireType(selector, SelectorResource, self.compileState)
            return ExecuteCommand.AT(target=selector)

        def absolute(x, y, z):
            return ExecuteCommand.POSITIONED(x=str(x), y=str(y), z=str(z))

        def relative(x, y, z):
            return ExecuteCommand.POSITIONED(x="~" + str(x), y="~" + str(y), z="~" + str(z))

        def local(x, y, z):
            return ExecuteCommand.POSITIONED(x="^" + str(x), y="^" + str(y), z="^" + str(z))

        command_table = {
            "context_for"     : for_,
            "context_at"      : at,
            "context_absolute": absolute,
            "context_relative": relative,
            "context_local"   : local
        }

        *modifiers, block = tree.children

        blockName = self.compileState.pushBlock(namespaceType=NamespaceType.CONTEXT_MANIPULATOR)
        self.visit_children(block)
        self.compileState.popBlock()

        command = ""
        for modifier in modifiers:
            self.compileState.currentTree = modifier
            name = modifier.data

            if name not in command_table:
                raise McScriptSyntaxError(f"Unknown modifier: '{name}'", self.compileState)

            args = [self.compileState.toResource(i) for i in modifier.children]
            command += command_table[name](*args)

        command = Command.EXECUTE(
            sub=command,
            command=Command.RUN_FUNCTION(function=blockName)
        )

        self.compileState.writeline(command)

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
