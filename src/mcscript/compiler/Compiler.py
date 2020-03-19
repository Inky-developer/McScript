import warnings
from typing import Dict

from lark import Tree, Token
from lark.visitors import Interpreter

from src.mcscript.Exceptions import McScriptNameError, McScriptArgumentsError, McScriptTypeError, \
    McScriptNotStaticError, McScriptIsStaticError
from src.mcscript.compiler import CompileState
from src.mcscript.compiler.tokenConverter import convertToken
from src.mcscript.data import defaultCode
from src.mcscript.data.Commands import Command, BinaryOperator, Relation, ExecuteCommand, Struct, UnaryOperator
from src.mcscript.data.Config import Config
from src.mcscript.data.builtins.builtins import BuiltinFunction
from src.mcscript.lang.Protocols.binaryOperatorProtocols import BinaryOperatorProtocol
from src.mcscript.lang.Protocols.unaryOperatorProtocols import UnaryNumberOperatorProtocol, \
    UnaryNumberVariableOperatorProtocol
from src.mcscript.lang.Resource.BooleanResource import BooleanResource
from src.mcscript.lang.Resource.FunctionResource import Function
from src.mcscript.lang.Resource.ResourceBase import Resource, ValueResource
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
        if (var := self.compileState.currentNamespace()[varName]).isStatic:
            return var
        # stack = self.compileState.expressionStack.next()
        # self.compileState.writeline(Command.LOAD_VARIABLE(
        #     stack=stack,
        #     var=self.compileState.currentNamespace()[varName].value
        # ))
        # return stack
        var = self.compileState.currentNamespace()[varName]
        return var

    def unary_operation(self, tree):
        # ToDo: get rid of these awful protocols
        operator, value = tree.children
        value = self.compileState.toResource(value)
        operator = UnaryOperator(operator)

        if not isinstance(value, UnaryNumberVariableOperatorProtocol) or operator == UnaryOperator.MINUS:
            value = value.load(self.compileState)
        if isinstance(value, (UnaryNumberVariableOperatorProtocol, UnaryNumberOperatorProtocol)):
            return value.unaryOperation(operator, self.compileState)
        raise McScriptTypeError(f"Resource {repr(value)} does not support unary operations.")

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

            if not isinstance(number2, ValueResource):
                raise TypeError("Expected operand of type ValueResource")

            if isinstance(number1, BinaryOperatorProtocol):
                number1 = number1.numericOperation(number2, operator, self.compileState)
            else:
                raise TypeError(f"Expected operand that supports numeric operations, not {repr(number1)}")
        return number1

    def term(self, tree):
        # todo refactor this
        term = tree.children[0]
        if term.data in (
                "value", "function_call", "variable", "comparison",
                "control_execute"):  # this term does not contain operands
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

        if not isinstance(value, ValueResource):
            raise McScriptTypeError("can only assign values for variables", tree)

        if identifier in self.compileState.currentNamespace():
            stack = self.compileState.currentNamespace()[identifier]
        else:
            # create a new stack value
            stack = self.compileState.currentNamespace().variableFmt.format(identifier)
        if not hasattr(value, "storeToNbt"):
            var = value
            warnings.warn(
                "Every Resource should implement the storeToNbt function if it can be on both scoreboard and storage")
        else:
            var = value.storeToNbt(stack, self.compileState)
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
        if not isinstance(var, (BinaryOperatorProtocol, ValueResource)):
            raise McScriptTypeError(
                "Cannot do a term-in-place operation with a variable that does not support numerical operations",
                tree
            )
        if var.isStatic:
            raise McScriptIsStaticError("Cannot modify a static variable", tree)
        if not isinstance(resource, ValueResource):
            raise AttributeError(f"Cannot do an operation with '{resource}'")

        var = var.numericOperation(resource, BinaryOperator(operator), self.compileState)

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
        addr_condition = self.visit(condition)
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
        address = self.compileState.load(tree.children[0])
        if not isinstance(address, ValueResource):
            raise McScriptTypeError("return value must be a ValueResource", tree)
        # set the return resource in the current namespace
        if address.hasStaticValue:
            self.compileState.writeline(Command.SET_VALUE(
                stack=self.compileState.config.RETURN_SCORE,
                value=int(address)
            ))
        else:
            self.compileState.writeline(Command.SET_RETURN_VALUE(
                stack=address
            ))

    def function_parameter(self, tree):
        identifier, datatype = tree.children
        datatype = convertToken(datatype, self.compileState)
        return identifier, datatype

    def function_definition(self, tree):
        function_name, parameter_list, returnType, block = tree.children
        is_special = function_name in defaultCode.MAGIC_FUNCTIONS

        parameter_list = [self.visit(i) for i in parameter_list.children]
        function = Function(str(function_name), convertToken(returnType, self.compileState), parameter_list)
        self.compileState.currentNamespace().addFunction(function)
        self.compileState.nextNamespaceDefaults = function.parameters

        # custom block parsing for easier return and recursion handling
        # ToDo: recursion maybe?
        blockName = self.compileState.codeBlockStack.next()
        self.compileState.fileStructure.pushFile(blockName)
        self.compileState.pushStack()
        newNamespace = self.compileState.currentNamespace()
        function.namespace = newNamespace
        function.blockName = blockName
        if is_special:
            param_count = defaultCode.MAGIC_FUNCTIONS[function_name]
            if param_count != len(function.parameters):
                raise McScriptArgumentsError(
                    f"Magic method {function.name()} must accept exactly {param_count} parameters")
            self.compileState.fileStructure.setPoi(function)
        self.visit_children(block)
        self.compileState.popStack()
        self.compileState.fileStructure.popFile()

    def function_value(self, tree):
        value, = tree.children
        return self.compileState.toResource(value)

    def builtinFunction(self, function: BuiltinFunction, *parameters: Resource):
        parameters = [self.visit(i) for i in parameters]
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
        for parameter, param_data in zip(parameters, function.parameters):
            param_name, param_type = param_data
            p_address = function.namespace[param_name]
            parameter = self.compileState.toResource(parameter)
            if parameter.hasStaticValue:
                self.compileState.writeline(
                    Command.SET_VARIABLE(struct=Struct.VAR(var=str(p_address), value=parameter.toNumber())))
            else:
                self.compileState.writeline(Command.SET_VARIABLE_FROM(
                    var=p_address.value,
                    command=Command.GET_SCOREBOARD_VALUE(stack=parameter)
                ))
        self.compileState.writeline(Command.RUN_FUNCTION(function=function.blockName))

        stack = self.compileState.expressionStack.next()
        self.compileState.writeline(Command.SET_VALUE_EQUAL(
            stack=stack,
            stack2=self.compileState.config.RETURN_SCORE
        ))

        return function.returnType(stack, False)

    def function_call(self, tree):
        function_name, *parameters = tree.children
        function = self.compileState.currentNamespace()[function_name]
        if isinstance(function, BuiltinFunction):
            return self.builtinFunction(function, *parameters)
        if not isinstance(function, Function):
            raise TypeError("Can this error even happen?")
        return self.userFunction(function, *parameters)

    def at(self, tree):
        target, block = tree.children
        block, namespace = self.visit(block)
        self.compileState.writeline(Command.EXECUTE(
            sub=ExecuteCommand.AT(target=target),
            command=Command.RUN_FUNCTION(function=block)
        ))

    def as_(self, tree):
        target, block = tree.children
        block, namespace = self.visit(block)
        self.compileState.writeline(Command.EXECUTE(
            sub=ExecuteCommand.AS(target=target),
            command=Command.RUN_FUNCTION(function=block)
        ))

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
