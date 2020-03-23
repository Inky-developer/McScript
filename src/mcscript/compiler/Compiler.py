import warnings
from typing import Dict

from lark import Tree, Token
from lark.visitors import Interpreter

from src.mcscript.Exceptions import McScriptNameError, McScriptArgumentsError, McScriptTypeError, \
    McScriptNotStaticError, McScriptIsStaticError, McScriptSyntaxError
from src.mcscript.compiler import CompileState
from src.mcscript.compiler.tokenConverter import convertToken
from src.mcscript.data import defaultCode, defaultEnums
from src.mcscript.data.Commands import Command, BinaryOperator, Relation, ExecuteCommand, UnaryOperator, \
    multiple_commands
from src.mcscript.data.Config import Config
from src.mcscript.data.builtins.builtins import BuiltinFunction
from src.mcscript.lang.Resource.AddressResource import AddressResource
from src.mcscript.lang.Resource.BooleanResource import BooleanResource
from src.mcscript.lang.Resource.FunctionResource import Function
from src.mcscript.lang.Resource.NbtAddressResource import NbtAddressResource
from src.mcscript.lang.Resource.NullResource import NullResource
from src.mcscript.lang.Resource.ResourceBase import Resource, ValueResource, ObjectResource
from src.mcscript.lang.Resource.StructResource import StructResource
from src.mcscript.lang.Resource.TypeResource import TypeResource
from src.mcscript.utils.Datapack import Datapack


class Compiler(Interpreter):
    def __init__(self, grammar):
        # noinspection PyTypeChecker
        self.compileState: CompileState = None

    def compile(self, tree: Tree, namespace: Dict[str, Resource], code: str, config: Config) -> Datapack:
        self.compileState = CompileState(code, self.visit, config)
        self.compileState.currentNamespace().namespace.update(namespace)
        self.compileState.fileStructure.pushFile("main.mcfunction")
        self.compileBuiltins()
        self.visit(tree)
        return self.compileState.datapack

    def compileBuiltins(self):
        BuiltinFunction.load(self)

    def loadFunction(self, function: BuiltinFunction):
        self.compileState.currentNamespace().addFunction(function)

    def value(self, tree):
        value = tree.children[0]
        if isinstance(value, Tree):
            return self.visit(value)
        elif isinstance(value, Token):
            return convertToken(value, self.compileState)
        raise McScriptNameError(f"Invalid value: {value}", value)

    def variable(self, tree):
        varName = tree.children[0]
        if varName not in self.compileState.currentNamespace():
            raise McScriptNameError(f"Unknown variable: {varName}", varName)
        if isinstance(var := self.compileState.currentNamespace()[varName], ValueResource) and var.isStatic:
            return var
        # stack = self.compileState.expressionStack.next()
        # self.compileState.writeline(Command.LOAD_VARIABLE(
        #     stack=stack,
        #     var=self.compileState.currentNamespace()[varName].value
        # ))
        # return stack
        var = self.compileState.currentNamespace()[varName]
        return var

    def property(self, tree):
        obj, *properties = tree.children

        if obj not in self.compileState.currentNamespace():
            # check if a default enum is accessed and, if yes, load it
            if str(obj) in defaultEnums.ENUMS:
                self.compileState.stack[0][obj] = defaultEnums.ENUMS[obj]()
            else:
                raise McScriptNameError(f"Unknown object: {obj}", tree)

        obj = self.compileState.currentNamespace()[obj]
        if not isinstance(obj, ObjectResource):
            raise McScriptTypeError(f"Resource {obj} is not an object.", tree)

        value = None
        for prop in properties:
            value = obj.getAttribute(prop)
        return value.load(self.compileState)

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
                raise McScriptTypeError(f"Could not perform operation {operator.name} on {repr(value)}")

    def boolean_and(self, tree):
        rest = tree.children

        _conditions = []
        while rest:
            a, _, b, *rest = rest
            _conditions.append(a)
            _conditions.append(b)

        conditions = []
        for condition in _conditions:
            condition = self.compileState.toResource(condition).convertToBoolean(self.compileState)
            if condition.isStatic:
                if condition.value:
                    continue
                return BooleanResource.FALSE
            conditions.append(condition)

        if not conditions:
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
                return BooleanResource.TRUE

            if operand1.isStatic and operand2.isStatic:
                continue

            conditions.append(operand1)
            conditions.append(operand2)

        if not conditions:
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
                number1 = number1.numericOperation(number2, operator, self.compileState)
            except NotImplementedError:
                raise TypeError(f"Expected operand that supports numeric operations, not {repr(number1)}")
        return number1

    def term(self, tree):
        # todo refactor this
        term = tree.children[0]
        if term.data in (
                "value", "function_call", "variable", "comparison",
                "control_execute", "property"):  # this term does not contain operands
            return self.visit(term)
        return self.binaryOperation(*self.visit_children(tree.children[0]))

    def comparison(self, tree):
        # ToDO: implement execute if matches
        left, operator, right = tree.children
        addr_left = self.compileState.load(left)
        if not isinstance(addr_left, ValueResource):
            raise McScriptTypeError("left comparison term must be a valueResource", tree)
        addr_right = self.compileState.load(right)
        if not isinstance(addr_right, ValueResource):
            raise McScriptTypeError("right comparison term must be a valueResource", tree)
        relation = Relation.get(operator.type)
        if addr_right.isStatic:
            addr_left, addr_right = addr_right, addr_left
            relation = relation.invert()

        if addr_left.isStatic and addr_right.isStatic:
            result = relation.testRelation(addr_left.value, addr_right.value)
            warnings.warn(f"comparison at {tree.line}:{tree.column} is always {result}.")
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
                    range=relation.invert().getRange(value)
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
        value = self.compileState.toResource(value)

        if identifier in self.compileState.currentNamespace():
            stack = self.compileState.currentNamespace()[identifier]
        else:
            # create a new stack value
            stack = NbtAddressResource(self.compileState.currentNamespace().variableFmt.format(identifier))
        try:
            # if the value is a variable, they cannot share the same stack
            if not isinstance(stack, (NbtAddressResource, AddressResource)):
                # if a variable is replaced, copy the resource to the variable
                var = value.copy(stack.value, self.compileState)
            else:
                var = value.load(self.compileState).storeToNbt(stack, self.compileState)
        except TypeError as e:
            var = value
            warnings.warn(
                "Every Resource should implement the storeToNbt function if it can be on both scoreboard and storage\n"
                f"({e})"
            )

        self.compileState.currentNamespace().setVar(identifier, var)
        return var

    def const_declaration(self, tree):
        declaration = tree.children[0]
        identifier, value = declaration.children
        value = self.compileState.toResource(value)

        if not isinstance(value, ValueResource):
            raise McScriptTypeError("Can only assign values for variables", tree)
        if not value.hasStaticValue:
            raise McScriptNotStaticError("static declaration needs a static value.", tree)

        self.compileState.currentNamespace()[identifier] = value

    def term_ip(self, tree):
        variable, operator, resource = tree.children
        resource = self.compileState.load(resource)
        varResource = self.compileState.currentNamespace()[variable]
        var = varResource.load(self.compileState)
        if var.isStatic:
            raise McScriptIsStaticError("Cannot modify a static variable", tree)
        if not isinstance(resource, ValueResource):
            raise AttributeError(f"Cannot do an operation with '{resource}'")

        try:
            var = var.numericOperation(resource, BinaryOperator(operator), self.compileState)
        except NotImplementedError:
            raise McScriptTypeError(
                f"in place operation: Failed because {repr(var)} does not support the operation {operator.name}"
            )

        # lastly, storeToNbt the value back into the variable
        self.compileState.writeline(Command.SET_VARIABLE_FROM(
            var=str(varResource),
            command=Command.GET_SCOREBOARD_VALUE(stack=var)
        ))

    def block(self, tree):
        blockName = self.compileState.pushBlock()
        newNamespace = self.compileState.currentNamespace()
        self.visit_children(tree)
        self.compileState.popBlock()
        return blockName, newNamespace

    def control_if(self, tree):
        # ToDO: reduce to one mcfunction statement
        condition, block, *block_else = tree.children
        addr_condition = self.compileState.load(condition)
        if not isinstance(addr_condition, ValueResource):
            raise McScriptTypeError("comparison result must be a valueResource", tree)

        if addr_condition.hasStaticValue:
            warnings.warn(f"If-statement at {tree.line}:{tree.column} is always {bool(int(addr_condition))}")
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
            block_else = block_else[0]
            blockName, _ = self.visit(block_else)
            self.compileState.writeline(Command.EXECUTE(
                sub=ExecuteCommand.UNLESS_SCORE_RANGE(
                    stack=addr_condition,
                    range=1
                ),
                command=Command.RUN_FUNCTION(function=blockName)
            ))

    def control_while(self, tree):
        _condition, block = tree.children
        condition = self.compileState.toResource(_condition)

        blockName = self.compileState.pushBlock()
        self.visit_children(block)
        infinite_loop = False
        if condition.hasStaticValue:
            infinite_loop = bool(condition.value)
            if infinite_loop:
                warnings.warn(f"Infinite loop at {tree.line}:{tree.column}")
            else:
                warnings.warn(f"Loop will never run at {tree.line}:{tree.column}")
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

    def return_(self, tree):
        resource = self.compileState.toResource(tree.children[0])
        if self.compileState.currentNamespace().returnedResource:
            raise McScriptSyntaxError("Cannot set the return value twice.", tree)
        self.compileState.currentNamespace().returnedResource = resource

    def function_parameter(self, tree):
        identifier, datatype = tree.children
        datatype = convertToken(datatype, self.compileState)
        return identifier, datatype

    def function_definition(self, tree):
        function_name, parameter_list, returnType, block = tree.children
        is_special = function_name in defaultCode.MAGIC_FUNCTIONS

        parameter_list = [self.visit(i) for i in parameter_list.children]
        if any(parameter.requiresInlineFunc for _, parameter in parameter_list):
            raise McScriptTypeError(F"Inline functions are yet to be implemented")

        # blockName = self.compileState.codeBlockStack.next()
        blockName = function_name if self.compileState.currentNamespace().index == 0 else \
            self.compileState.codeBlockStack.next()
        self.compileState.fileStructure.pushFile(blockName)
        self.compileState.pushStack()
        newNamespace = self.compileState.currentNamespace()

        function = Function(str(function_name), convertToken(returnType, self.compileState), parameter_list,
                            newNamespace, blockName)

        # set the parameters
        for identifier, resource in function.parameters:
            newNamespace[identifier] = resource.createEmptyResource(identifier, self.compileState)

        if is_special:
            param_count = defaultCode.MAGIC_FUNCTIONS[function_name]
            if param_count != len(function.parameters):
                raise McScriptArgumentsError(
                    f"Magic method {function.name()} must accept exactly {param_count} parameters")
            self.compileState.fileStructure.setPoi(function)

        # compile the function body
        self.visit_children(block)

        self.compileState.popStack()
        self.compileState.fileStructure.popFile()

        # add the function to the current namespace
        self.compileState.currentNamespace().addFunction(function)

    def function_value(self, tree):
        value, = tree.children
        return self.compileState.toResource(value)

    def builtinFunction(self, function: BuiltinFunction, *parameters: Resource):
        parameters = [self.compileState.load(i) for i in parameters]
        try:
            result = function.create(self.compileState, *parameters)
            if result.code:
                if result.inline:
                    self.compileState.writeline(result.code)
                else:
                    addr = self.compileState.pushBlock()
                    self.compileState.writeline(result.code)
                    self.compileState.popBlock()
                    self.compileState.writeline(Command.RUN_FUNCTION(function=addr))
        except TypeError:
            raise McScriptArgumentsError(f"Invalid number of arguments for function '{function.name()}'")

        return result.resource

    def userFunction(self, function: Function, *parameters):
        if len(parameters) != len(function.parameters):
            raise McScriptArgumentsError(
                f"Invalid arguments: required {len(function.parameters)} but got {len(parameters)}")

        for parameter, p_data in zip(parameters, function.parameters):
            param_name, param_type = p_data

            p_address = function.namespace[param_name]
            parameter = self.compileState.toResource(parameter)

            if parameter.type() != param_type.type():
                raise McScriptArgumentsError(
                    f"{repr(function)} got argument {parameter} with invalid type {parameter.type().value}, "
                    f"expected {param_type.type().value}"
                )

            try:
                parameter.copy(p_address.value, self.compileState)
            except TypeError:
                parameter.load(self.compileState).copy(p_address.value, self.compileState)
        self.compileState.writeline(Command.RUN_FUNCTION(function=function.blockName))

        returnValue = function.namespace.returnedResource or NullResource()
        if returnValue.type() != function.returnType.type():
            raise McScriptTypeError(f"{repr(function)} should return {function.returnType.type().value} "
                                    f"but returned {returnValue.type().value}")
        return returnValue

    def function_call(self, tree):
        function_name, *parameters = tree.children
        function = self.compileState.currentNamespace()[function_name]
        if isinstance(function, BuiltinFunction):
            return self.builtinFunction(function, *parameters)
        if isinstance(function, Function):
            return self.userFunction(function, *parameters)
        # if the function is neither a builtin function nor a user function
        # the given resource might implement the operation_call method
        try:
            return function.operation_call(self.compileState, *parameters)
        except TypeError:
            raise McScriptTypeError(f"The resource {repr(function)} can not be treated like a function")

    def variable_declaration(self, tree):
        identifier, datatype = tree.children
        self.compileState.currentNamespace().setVar(identifier,
                                                    TypeResource(convertToken(datatype, self.compileState), True))

    def control_struct(self, tree):
        name, block = tree.children
        self.compileState.pushStack()
        namespace = self.compileState.currentNamespace()

        struct = StructResource(name, namespace, self.compileState.currentNamespace())
        self.compileState.currentNamespace().setVar(name, struct)

        for declaration in block.children:
            self.visit(declaration)

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
                raise McScriptSyntaxError(f"Repeated context modifier '{modifier} {selector}'", tree)
        self.compileState.writeline(Command.EXECUTE(sub=command, command=Command.RUN_FUNCTION(function=block)))

    def expression(self, tree):
        return self.visit(tree.children[0])

    def statement(self, tree):
        self.compileState.writeline(f"# {self.compileState.getDebugLines(tree.line, tree.end_line)}")
        res = self.visit_children(tree)
        # # now clear up the expression counter geht doch nicht so einfach
        # self.compileState.expressionStack.reset()
        # for readability
        self.compileState.writeline()
        return res
