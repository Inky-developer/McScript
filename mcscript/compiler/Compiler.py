from typing import List

from lark import Token, Tree
from lark.visitors import Interpreter

from mcscript import Logger
from mcscript.Exceptions.compileExceptions import McScriptArgumentsError, McScriptIsStaticError, McScriptNameError, \
    McScriptNotStaticError, McScriptSyntaxError, McScriptTypeError
from mcscript.compiler.CompileState import CompileState
from mcscript.compiler.NamespaceType import NamespaceType
from mcscript.compiler.tokenConverter import convertToken
from mcscript.data import defaultCode, defaultEnums
from mcscript.data.Config import Config
from mcscript.data.commands import BinaryOperator, Command, ExecuteCommand, Relation, UnaryOperator, multiple_commands
from mcscript.lang.builtins.builtins import BuiltinFunction
from mcscript.lang.resource.BooleanResource import BooleanResource
from mcscript.lang.resource.DefaultFunctionResource import DefaultFunctionResource
from mcscript.lang.resource.EnumResource import EnumResource
from mcscript.lang.resource.InlineFunctionResource import InlineFunctionResource
from mcscript.lang.resource.NbtAddressResource import NbtAddressResource
from mcscript.lang.resource.NullResource import NullResource
from mcscript.lang.resource.StructMethodResource import StructMethodResource
from mcscript.lang.resource.StructResource import StructResource
from mcscript.lang.resource.TypeResource import TypeResource
from mcscript.lang.resource.base.FunctionResource import Parameter
from mcscript.lang.resource.base.ResourceBase import ObjectResource, Resource, ValueResource
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

    def compile(self, tree: Tree, code: str, config: Config) -> Datapack:
        self.compileState = CompileState(code, self.visit, config)
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

        enum = EnumResource(*properties, **value_properties)
        self.compileState.currentNamespace()[name] = enum

    def enum_block(self, tree):
        properties = []
        value_properties = {}

        for name, *value in self.visit_children(tree):
            if value:
                value_properties[name] = value[0]
            else:
                properties.append(name)

        return properties, value_properties

    def enum_property(self, tree):
        identifier, *value = tree.children
        if value:
            return identifier, convertToken(value[0], self.compileState)
        return identifier

    def accessor(self, tree):
        """
        a variable or a list of dot separated names like a.b.c will be loaded here.

        Returns:
            a list of all objects that were accessed
        """
        ret, *values = tree.children
        if ret not in self.compileState.currentNamespace():
            if result := defaultEnums.get(ret):
                self.compileState.stack[0][ret] = result
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

        _conditions = []
        while rest:
            a, _, b, *rest = rest
            _conditions.append(a)
            _conditions.append(b)

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

        conditions = []

        while rest:
            operand1, _, operand2, *rest = rest
            operand1 = self.compileState.toResource(operand1).convertToBoolean(self.compileState)
            operand2 = self.compileState.toResource(operand2).convertToBoolean(self.compileState)

            if (operand1.isStatic and operand1.value) or (operand2.isStatic and operand2.value):
                Logger.warn(f"[Compiler] boolean or at {tree.line}:{tree.column} is always True.")
                return BooleanResource.TRUE

            if operand1.isStatic and operand2.isStatic:
                continue

            conditions.append(operand1)
            conditions.append(operand2)

        if not conditions:
            Logger.warn(f"[Compiler] boolean or at {tree.line}:{tree.column} is always False.")
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
        # ToDO: optimization for operations like a*a
        # for this there must be an option that the number1 loads number1 and number2 manually
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
        # ToDo: comparison code is awful currently.
        # ToDo: Also it must be more efficient (double copying of values)
        left, operator, right = tree.children
        addr_left = self.compileState.load(left)
        if not isinstance(addr_left, ValueResource):
            raise McScriptTypeError("left comparison term must be a valueResource", self.compileState)
        addr_right = self.compileState.load(right)
        if not isinstance(addr_right, ValueResource):
            raise McScriptTypeError("right comparison term must be a valueResource", self.compileState)
        relation = Relation.get(operator.type)
        if addr_right.isStatic:
            addr_left, addr_right = addr_right, addr_left
            relation = relation.swap()

        if addr_left.isStatic and addr_right.isStatic:
            result = relation.testRelation(addr_left.value, addr_right.value)
            Logger.warn(f"[Compiler] comparison at {tree.line}:{tree.column} is always {result}.")
            return BooleanResource(result, True)
        addr_result = self.compileState.expressionStack.next()
        self.compileState.writeline(Command.SET_VALUE(
            stack=addr_result,
            value=0
        ))
        if addr_left.isStatic:
            # if one of both terms is static
            # currently only implemented for numbers
            value = int(addr_left.toNumber())
            scoreTest = ExecuteCommand.IF_SCORE_RANGE if relation != Relation.NOT_EQUAL else \
                ExecuteCommand.UNLESS_SCORE_RANGE
            self.compileState.writeline(Command.EXECUTE(
                sub=scoreTest(
                    stack=str(addr_right),
                    range=relation.swap().getRange(value)
                ),
                command=Command.SET_VALUE(stack=addr_result, value=1)
            ))
            return BooleanResource(addr_result, False)

        # else as normal - no side of the comparison is known
        if relation == Relation.NOT_EQUAL:
            command = Command.EXECUTE(
                sub=ExecuteCommand.UNLESS_SCORE(
                    stack=addr_left,
                    relation=Relation.EQUAL.value,
                    stack2=addr_right
                ),
                command=Command.SET_VALUE(
                    stack=addr_result,
                    value=1
                )
            )
        else:
            command = Command.EXECUTE(
                sub=ExecuteCommand.IF_SCORE(
                    stack=addr_left,
                    relation=relation.value,
                    stack2=addr_right
                ),
                command=Command.SET_VALUE(
                    stack=addr_result,
                    value=1
                )
            )
        self.compileState.writeline(command)
        return BooleanResource(addr_result, False)

    def declaration(self, tree):
        identifier, value = tree.children
        if len(identifier.children) != 1:
            return self.propertySetter(tree)
        identifier, = identifier.children
        value = self.compileState.toResource(value)

        if identifier in self.compileState.currentNamespace():
            stack = self.compileState.currentNamespace()[identifier]
            if isinstance(stack, ValueResource):
                stack = stack.value
            elif isinstance(stack, ObjectResource):
                try:
                    stack = stack.getBasePath()
                except TypeError:
                    stack = NbtAddressResource(self.compileState.currentNamespace().variableFmt.format(identifier))
            else:
                stack = NbtAddressResource(self.compileState.currentNamespace().variableFmt.format(identifier))
        else:
            # create a new stack value
            stack = NbtAddressResource(self.compileState.currentNamespace().variableFmt.format(identifier))
        try:
            var = value.load(self.compileState).storeToNbt(stack, self.compileState)
        except TypeError as e:
            var = value
            # The null resource is kinda special because it only ever has one value
            if not isinstance(value, NullResource):
                raise McScriptTypeError(f"Could not assign type {value.type().value} to a variable because "
                                        f"it does not support this operation", self.compileState)
        self.compileState.currentNamespace().setVar(identifier, var)
        return var

    def const_declaration(self, tree):
        declaration = tree.children[0]
        identifier, value = declaration.children
        if len(identifier.children) > 1:
            raise McScriptSyntaxError(f"Cannot set a const value on an object.", self.compileState)
        identifier, = identifier.children
        value = self.compileState.toResource(value)

        if not isinstance(value, ValueResource):
            raise McScriptTypeError(f"Only simple datatypes can be assigned using const, not {value}",
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
        # ToDO: reduce to one mcfunction statement
        _, condition, block, *block_else = tree.children

        if not block.children:
            Logger.debug(f"[Compiler] skipping if-statement line {tree.line}: empty block")
            return None

        addr_condition = self.compileState.load(condition).convertToBoolean(self.compileState)
        if not isinstance(addr_condition, ValueResource):
            raise McScriptTypeError("comparison result must be a valueResource", self.compileState)

        if addr_condition.hasStaticValue:
            Logger.warn(f"[Compiler] If-statement at {tree.line}:{tree.column} is always {bool(int(addr_condition))}")
            if int(addr_condition):
                run = block
            else:
                run = block_else

            if run:
                blockName, _ = self.visit(run)
                self.compileState.writeline(Command.RUN_FUNCTION(function=blockName))
            return

        # else normal if statement

        blockName, _ = self.visit(block)

        self.compileState.writeline(Command.EXECUTE(
            sub=ExecuteCommand.IF_SCORE_RANGE(
                stack=addr_condition,
                range=1
            ),
            command=Command.RUN_FUNCTION(function=blockName)
        ))

        if block_else:
            _, block_else = block_else
            blockName, _ = self.visit(block_else)
            self.compileState.writeline(Command.EXECUTE(
                sub=ExecuteCommand.UNLESS_SCORE_RANGE(
                    stack=addr_condition,
                    range=1
                ),
                command=Command.RUN_FUNCTION(function=blockName)
            ))

    def control_while(self, tree):
        _, _condition, block = tree.children
        condition = self.compileState.toResource(_condition)

        blockName = self.compileState.pushBlock()
        self.visit_children(block)
        infinite_loop = False
        if not isinstance(condition, ValueResource):
            raise McScriptTypeError(f"invalid condition {condition}", self.compileState)
        if condition.hasStaticValue:
            infinite_loop = bool(condition.value)
            if infinite_loop:
                Logger.warn(f"[Compiler] Infinite loop at {tree.line}:{tree.column}")
            else:
                Logger.warn(f"[Compiler] Loop will never run at {tree.line}:{tree.column}")
                return

        if not infinite_loop:
            # check the condition
            addr_expression = self.compileState.load(_condition)
            self.compileState.writeline(Command.EXECUTE(
                sub=ExecuteCommand.IF_SCORE_RANGE(
                    stack=addr_expression,
                    range=1
                ),
                command=Command.RUN_FUNCTION(function=blockName)
            ))
        else:
            self.compileState.writeline(Command.RUN_FUNCTION(function=blockName))
        self.compileState.popBlock()

        # next line unnecessary?
        if not infinite_loop:
            addr_expression = self.compileState.load(condition)
            self.compileState.writeline(Command.EXECUTE(
                sub=ExecuteCommand.IF_SCORE_RANGE(
                    stack=addr_expression,
                    range=1
                ),
                command=Command.RUN_FUNCTION(function=blockName)
            ))
        else:
            self.compileState.writeline(Command.RUN_FUNCTION(function=blockName))

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
        return_type = TypeResource(convertToken(return_type, self.compileState), True)
        if any(parameter.value.requiresInlineFunc for _, parameter in parameter_list) and not inline:
            raise McScriptTypeError(f"Some parameters can only be used in an inline context. "
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
        modifier, identifier, datatype = tree.children
        self.compileState.currentNamespace()[identifier] = TypeResource(
            convertToken(datatype, self.compileState), True, modifier
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
        command_table = {
            "for": ExecuteCommand.AS,
            "at": ExecuteCommand.AT
        }
        *modifier_list, block = tree.children
        block, namespace = self.visit(block)
        command = ""
        for modifier, selector in zip(modifier_list[-2::-2], modifier_list[-1::-2]):
            try:
                if not command:
                    command = command_table.pop(modifier)(target=selector)
                else:
                    command = command_table.pop(modifier)(target=selector, command=command)
            except KeyError:
                raise McScriptSyntaxError(f"Repeated context modifier '{modifier} {selector}'", self.compileState)
        self.compileState.writeline(Command.EXECUTE(sub=command, command=Command.RUN_FUNCTION(function=block)))

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
