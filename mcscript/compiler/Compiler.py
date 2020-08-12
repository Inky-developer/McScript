from typing import Dict, Tuple

from lark import Token, Tree
from lark.visitors import Interpreter

from mcscript.analyzer.Analyzer import NamespaceContext
from mcscript.compiler.CompileState import CompileState
from mcscript.compiler.ContextType import ContextType
from mcscript.compiler.common import conditional_loop, get_property, readContextManipulator, set_property, set_variable
from mcscript.compiler.tokenConverter import convert_token_to_resource, convert_token_to_type
from mcscript.data.Config import Config
from mcscript.exceptions.compileExceptions import (McScriptDeclarationError, McScriptNameError, McScriptSyntaxError,
                                                   McScriptTypeError)
from mcscript.ir.IrMaster import IrMaster
from mcscript.ir.command_components import BinaryOperator, ScoreRange, ScoreRelation, UnaryOperator
from mcscript.ir.components import (ConditionalNode, ExecuteNode, FunctionCallNode, InvertNode, ScoreboardInitNode,
                                    StoreFastVarFromResultNode, StoreFastVarNode, IfNode)
from mcscript.lang import std
from mcscript.lang.atomic_types import Null
from mcscript.lang.resource.BooleanResource import BooleanResource
from mcscript.lang.resource.EnumResource import EnumResource
from mcscript.lang.resource.FunctionResource import FunctionResource
from mcscript.lang.resource.StructResource import StructResource
from mcscript.lang.resource.TupleResource import TupleResource
from mcscript.lang.resource.TypeResource import TypeResource
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
from mcscript.lang.resource.base.functionSignature import FunctionSignature, FunctionParameter


class Compiler(Interpreter):
    def __init__(self):
        # noinspection PyTypeChecker
        self.compileState: CompileState = None

    def visit(self, tree):
        previous = self.compileState.currentTree
        try:
            self.compileState.currentTree = tree
        except AttributeError:
            raise ValueError(
                "Cannot visit without a compile state. Use ´compile´ instead.")

        result = super().visit(tree)
        self.compileState.currentTree = previous
        return result

    def compile(self, tree: Tree, contexts: Dict[Tuple[int, int], NamespaceContext], code: str,
                config: Config) -> IrMaster:
        self.compileState = CompileState(code, contexts, self.visit, config)

        # load the stdlib - for now just builtins
        builtins = std.include()
        for builtin in builtins:
            self.compileState.currentContext().add_var(builtin.name, builtin)

        with self.compileState.ir.with_function(self.compileState.resource_specifier_main("main")):
            self.compileState.pushContext(ContextType.GLOBAL, 0, 0)
            self.visit(tree)

        with self.compileState.ir.with_function(self.compileState.resource_specifier_main("init_scoreboards")):
            for scoreboard in self.compileState.scoreboards:
                self.compileState.ir.append(ScoreboardInitNode(scoreboard))

        self.compileState.ir.optimize()

        for function_node in self.compileState.ir.function_nodes:
            print(function_node)
        # return self.compileState.datapack
        return self.compileState.ir

    #######################
    #    tree handlers    #
    #######################
    def boolean_constant(self, tree):
        return BooleanResource(tree.children[0] == "True", None)

    def value(self, tree):
        """ a value is a simple token or expression that can be converted to a resource"""
        value = tree.children[0]

        if isinstance(value, Tree):
            ret = self.visit(value)
            return ret
        elif isinstance(value, Token):
            return convert_token_to_resource(value, self.compileState)
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
                raise McScriptNameError(
                    f"Enum member {name} was already defined for this enum", self.compileState)
            if value:
                value_properties[name] = value[0]
            else:
                properties.append(name)

        return properties, value_properties

    def enum_property(self, tree):
        identifier, *value = tree.children
        if value:
            return identifier, convert_token_to_resource(value[0], self.compileState)
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
            raise McScriptTypeError(
                f"{accessor.type().value} does not support reading index access", self.compileState)

    def index_setter(self, tree):
        accessor, index, value = tree.children

        accessor = self.visit(accessor)
        index = self.compileState.toResource(index)
        value = self.compileState.toResource(value)

        try:
            return accessor.operation_set_element(self.compileState, index, value)
        except TypeError:
            raise McScriptTypeError(
                f"{accessor.type().value} does not support writing index access", self.compileState)

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
            raise ValueError(
                f"Unknown unary operator {operator.name} in unary_operation")

        operator, value = tree.children
        value = self.compileState.toResource(value)
        operator = UnaryOperator(operator)

        # first try to do the operation on the resource itself.
        # if that is not possible, load the resource and try again
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
            condition = self.compileState.load(
                condition)
            if not isinstance(condition, BooleanResource):
                raise McScriptTypeError(f"Expected bool, got {condition.type()}", self.compileState)
            if condition.is_static:
                if condition.static_value:
                    continue
                return BooleanResource(False, None)
            conditions.append(condition)

        if not conditions:
            return BooleanResource(True, None)

        stack = self.compileState.expressionStack.next()

        # None of the conditions will be static
        condition_node = ConditionalNode(
            [ConditionalNode.IfScoreMatches(condition.scoreboard_value, ScoreRange(1), False)
             for condition in conditions]
        )

        self.compileState.ir.append_all(
            StoreFastVarNode(stack, 0),
            IfNode(condition_node, StoreFastVarNode(stack, 1))
        )

        return BooleanResource(None, stack)

    def boolean_or(self, tree):
        rest = tree.children

        _conditions = [rest[0]]
        rest = rest[1:]
        while rest:
            _, a, *rest = rest
            _conditions.append(a)
        conditions = []

        for condition in _conditions:
            value = self.compileState.toResource(
                condition)
            if not isinstance(value, BooleanResource):
                raise McScriptTypeError(f"Expected bool, got {value.type()}", self.compileState)
            if value.is_static:
                if value.static_value:
                    return BooleanResource(True, None)
                # always False boolean does not matter, so it will be discarded
                continue

            conditions.append(value)

        if not conditions:
            return BooleanResource(False, None)

        stack = self.compileState.expressionStack.next()

        # If there are still conditions left, none of them are static
        if conditions:
            self.compileState.ir.append(StoreFastVarNode(stack, 0))
            self.compileState.ir.append_all(
                IfNode(
                    ConditionalNode(
                        [ConditionalNode.IfScoreMatches(
                            condition.scoreboard_value,
                            ScoreRange(1),
                            False
                        )]),
                    StoreFastVarNode(stack, 1)
                ) for condition in conditions)

            return BooleanResource(None, stack)

    def boolean_not(self, tree):
        _, value = tree.children
        value = self.compileState.toResource(
            value)
        if not isinstance(value, BooleanResource):
            raise McScriptTypeError(f"Expected bool, got {value.type()}", self.compileState)

        if value.is_static:
            return BooleanResource(not value.static_value, None)

        stack = self.compileState.expressionStack.next()
        self.compileState.ir.append(InvertNode(value.scoreboard_value, value.scoreboard_value))
        return BooleanResource(None, stack)

    def binaryOperation(self, *args):
        number1, *values = args

        # whether the first number may be overwritten
        is_temporary = False

        # the first number can also be a list. Then just do a binary operation with it
        if isinstance(number1, list):
            number1 = self.binaryOperation(*number1)
            is_temporary = True

        number1 = self.compileState.load(number1)

        # by default all operations are in-place. This is not wanted, so the resource is copied
        if isinstance(number1, ValueResource) and not number1.is_static and not is_temporary:
            assign_resource = self.compileState.get_global_data("assign_resource")
            if isinstance(assign_resource, ValueResource) and not assign_resource.is_static:
                assign_stack = assign_resource.scoreboard_value
            else:
                assign_stack = self.compileState.expressionStack.next()
            number1 = number1.copy(assign_stack, self.compileState)

        for i in range(0, len(values), 2):
            operator, number2, = values[i:i + 2]

            if isinstance(number2, list):
                # number2 is now also temporary, but is will not change anyways
                number2 = self.binaryOperation(*number2)

            # get the operator enum type
            operator = BinaryOperator(operator)

            number2 = self.compileState.load(number2)

            if not isinstance(number2, ValueResource):
                raise ValueError(
                    "ToDO: Implement boolean operations for non value-resources")

            try:
                number1 = number1.numericOperation(
                    number2, operator, self.compileState)
            except TypeError:
                raise McScriptTypeError(
                    f"The Operation {operator.value} is not supported between {number1.type()} and "
                    f"{number2.type()}",
                    self.compileState)

        return number1

    def term(self, tree):
        term = tree.children[0]
        if term.data in ("sum", "product"):  # this term does not contain operands
            return self.binaryOperation(*self.visit_children(tree.children[0]))
        return self.visit(term)

    def comparison(self, tree):
        token_a, token_operator, token_b = tree.children

        a = self.compileState.toResource(token_a)
        b = self.compileState.toResource(token_b)
        operator = ScoreRelation(token_operator)

        try:
            node = a.operation_test_relation(self.compileState, operator, b)
        except TypeError:
            raise McScriptTypeError(
                f"Relation {operator.name} is not defined for {a.type()} and {b.type()}",
                self.compileState
            )

        if len(node["conditions"]) == 1 and isinstance(node["conditions"][0], ConditionalNode.IfBool):
            cond = node["conditions"][0]
            return BooleanResource(cond["val"], None)

        stack = self.compileState.expressionStack.next()
        self.compileState.ir.append(StoreFastVarFromResultNode(
            stack,
            node
        ))
        return BooleanResource(None, stack)

    def declaration(self, tree):
        identifier, _value = tree.children
        if len(identifier.children) != 1:
            return self.propertySetter(tree)

        identifier, = identifier.children

        # if an operation happens, the variable to store to is needed
        resource = self.compileState.currentContext().find_resource(identifier)
        with self.compileState.new_global_data("assign_resource", resource):
            value = self.compileState.toResource(_value)

        self.compileState.currentTree = _value
        set_variable(self.compileState, identifier, value)

    def multi_declaration(self, tree):
        *variables, expression = tree.children
        expression = self.compileState.toResource(expression)

        if not isinstance(expression, TupleResource):
            raise McScriptTypeError(
                f"Return type deconstruction works only for arrays, but not for type {expression.type()}",
                self.compileState
            )

        if (size := expression.size()) != len(variables):
            raise McScriptDeclarationError(
                f"Tuple must contain exactly {len(variables)} elements but found {size}:\n"
                f'({", ".join(str(i.type()) for i in expression.resources)})',
                self.compileState
            )

        for variable, value in zip(variables, expression.resources):
            variable, = variable.children
            set_variable(self.compileState, variable, value)

    def static_declaration(self, tree):
        raise NotImplementedError("Static declarations are shelved.")

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
            raise McScriptTypeError(
                f"in-place operation: Expected value, got {expression}", self.compileState)

        # do the numeric operation
        result = resource.numericOperation(
            expression,
            BinaryOperator(operator),
            self.compileState
        )

        # store the result back
        set_property(self.compileState, accessor, result)

    def control_if(self, tree):
        # ToDO: This could quite easily turned into an expression
        condition, block, block_else = tree.children

        condition_boolean = self.compileState.toResource(
            condition)

        if not isinstance(condition_boolean, BooleanResource):
            raise McScriptTypeError(f"Expected bool, got {condition_boolean.type()}", self.compileState)

        if condition_boolean.static_value is not None:
            line_and_column = (block.line, block.column) if condition_boolean else (block_else.line, block_else.column)
            with self.compileState.pushContext(ContextType.BLOCK, *line_and_column):
                if condition_boolean.static_value is True:
                    self.visit_children(block)
                else:
                    self.visit_children(block_else)
                return

        self.compileState.pushContext(ContextType.CONDITIONAL, block.line, block.column)
        with self.compileState.ir.with_buffer() as pos_branch:
            self.visit_children(block)
        self.compileState.popContext()
        pos_branch, = pos_branch

        if block_else is not None:
            self.compileState.pushContext(ContextType.CONDITIONAL, block_else.line, block_else.column)
            with self.compileState.ir.with_buffer() as neg_branch:
                self.visit_children(block_else)
            self.compileState.popContext()
            neg_branch, = neg_branch
        else:
            neg_branch = None

        self.compileState.ir.append(IfNode(
            ConditionalNode([ConditionalNode.IfScoreMatches(
                condition_boolean.scoreboard_value, ScoreRange(0), True)]),
            pos_branch,
            neg_branch
        ))

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
            raise McScriptTypeError(
                f"type {resource.type()} does not support iteration", self.compileState)

    def return_(self, tree):
        # ToDO: make return an ir node
        resource = self.compileState.toResource(tree.children[0])
        if self.compileState.currentContext().return_resource is not None:
            raise McScriptSyntaxError(
                "Cannot set the return value twice.", self.compileState)
        self.compileState.currentContext().return_resource = resource

    def function_parameter(self, tree):
        identifier, datatype = tree.children
        datatype = convert_token_to_type(datatype, self.compileState)
        return identifier, datatype

    def function_definition(self, tree):
        _, function_name, parameter_list, return_type, block = tree.children

        self_type_token, *parameters = parameter_list.children
        parameter_list = [self.visit(i) for i in parameters]

        # if self is specified, this function becomes a method and accepts an implicit first argument
        self_type = None
        if self_type_token is not None:
            self_resource = self.compileState.get_global_data("struct")
            if self_resource is None:
                self.compileState.currentTree = self_type_token
                raise McScriptDeclarationError("self is only allowed inside a struct", self.compileState)
            if not isinstance(self_resource, StructResource):
                raise ValueError("Internal Error, some idiot messed something up")
            self_type = self_resource.object_type

        # the return type can be omitted. In this case, it will be Null
        return_type = convert_token_to_type(return_type, self.compileState) if return_type else Null

        function = FunctionResource(
            function_name,
            FunctionSignature(
                [FunctionParameter(ident, rtype) for ident, rtype in parameter_list],
                return_type,
                function_name,
                self_type=self_type
            ),
            block
        )

        self.compileState.currentContext().add_var(function_name, function)

    def function_call(self, tree):
        function_name, *parameters = tree.children
        *accessed_objects, function = get_property(self.compileState, function_name)

        visited_params = [self.visit(i) for i in parameters]

        # any object that implements the call operator can be called. This of course includes function resources.
        try:
            return function.operation_call(self.compileState, *visited_params)
        except TypeError:
            raise McScriptTypeError(f"'{str(function)}' can not be treated like a function",
                                    self.compileState)

    def variable_declaration(self, tree):
        identifier, datatype = tree.children
        self.compileState.currentContext().add_var(identifier, TypeResource(
            convert_token_to_type(datatype, self.compileState)
        ))

    def control_struct(self, tree):
        name, block = tree.children
        self.compileState.pushContext(
            ContextType.OBJECT, block.line, block.column)
        context = self.compileState.currentContext()

        struct = StructResource(name, context, self.compileState)
        self.compileState.currentContext().add_var(name, struct)

        with self.compileState.new_global_data("struct", struct):
            for declaration in block.children:
                self.visit(declaration)
        self.compileState.popContext()
        self.compileState.currentContext().add_var(name, struct)

    def context_manipulator(self, tree: Tree):
        *modifiers, block = tree.children

        with self.compileState.node_block(ContextType.CONTEXT_MANIPULATOR, block.line, block.column) as block_name:
            self.visit_children(block)

        self.compileState.ir.append(ExecuteNode(
            readContextManipulator(modifiers, self.compileState),
            [FunctionCallNode(
                self.compileState.ir.find_function_node(block_name))]
        ))

    def expression(self, tree):
        return self.visit(tree.children[0])

    def statement(self, tree):
        # self.compileState.writeline(f"# {self.compileState.getDebugLines(tree.meta.line, tree.meta.end_line)}")
        res = self.visit_children(tree)
        # # now clear up the expression counter
        # self.compileState.expressionStack.reset()
        return res
