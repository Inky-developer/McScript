from typing import Dict, Tuple

from lark import Tree, Token
from lark.visitors import Interpreter

from mcscript.analyzer.Analyzer import NamespaceContext
from mcscript.compiler.CompileState import CompileState
from mcscript.compiler.ContextType import ContextType
from mcscript.compiler.common import conditional_loop, get_property, readContextManipulator, set_property, set_variable
from mcscript.compiler.tokenConverter import convert_token_to_resource, convert_token_to_type
from mcscript.data.Config import Config
from mcscript.exceptions.McScriptException import McScriptError
from mcscript.exceptions.exceptions import (McScriptUnexpectedTypeError, McScriptEnumValueAlreadyDefinedError,
                                            McScriptUnsupportedOperationError, McScriptDeclarationError,
                                            McScriptArgumentError)
from mcscript.ir.IrMaster import IrMaster
from mcscript.ir.command_components import BinaryOperator, ScoreRange, ScoreRelation, UnaryOperator
from mcscript.ir.components import (ConditionalNode, ExecuteNode, FunctionCallNode, InvertNode,
                                    StoreFastVarFromResultNode, StoreFastVarNode, IfNode)
from mcscript.lang import std, atomic_types
from mcscript.lang.atomic_types import Null, Bool
from mcscript.lang.resource.BooleanResource import BooleanResource
from mcscript.lang.resource.EnumResource import EnumResource
from mcscript.lang.resource.FunctionResource import FunctionResource
from mcscript.lang.resource.StructResource import StructResource
from mcscript.lang.resource.TupleResource import TupleResource
from mcscript.lang.resource.TypeResource import TypeResource
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
from mcscript.lang.resource.base.functionSignature import FunctionSignature, FunctionParameter
from mcscript.lang.utility import is_static


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
            self.compileState.push_context(ContextType.GLOBAL, 0, 0)
            self.visit(tree)

        self.compileState.ir.optimize()

        # for function in self.compileState.ir.function_nodes:
        #     print(function)

        return self.compileState.ir

    #######################
    #    tree handlers    #
    #######################
    def boolean_constant(self, tree):
        return BooleanResource(int(tree.children[0] == "True"), None)

    def value(self, tree):
        """ a value is a simple token or expression that can be converted to a resource"""
        value = tree.children[0]

        if isinstance(value, Tree):
            ret = self.visit(value)
            return ret
        elif isinstance(value, Token):
            return convert_token_to_resource(value, self.compileState)
        raise ValueError(f"Unknown value: {value}")

    def tuple(self, tree):
        elements = [self.visit(i) for i in tree.children]
        return TupleResource(*elements)

    # enums
    def control_enum(self, tree):
        _, name, block = tree.children
        try:
            properties, value_properties = self.visit(block)
        except ValueError as e:
            raise McScriptEnumValueAlreadyDefinedError(name, e.args[0], self.compileState)

        try:
            enum = EnumResource(*properties, **value_properties)
        except TypeError as e:
            raise McScriptUnexpectedTypeError(e.args[0], e.args[1], "ValueResource", self.compileState)

        self.compileState.currentContext().add_var(name, enum)

    def enum_block(self, tree):
        properties = []
        value_properties = {}

        for child in tree.children:
            name, *value = self.visit(child)

            if name in properties:
                raise ValueError(name)
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
            raise McScriptUnsupportedOperationError("[]", accessor.type(), None, self.compileState)

    def index_setter(self, tree):
        accessor, index, value = tree.children

        accessor = self.visit(accessor)
        index = self.compileState.toResource(index)
        value = self.compileState.toResource(value)

        try:
            return accessor.operation_set_element(self.compileState, index, value)
        except TypeError:
            raise McScriptUnsupportedOperationError("[]=", accessor.type(), None, self.compileState)

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
            raise McScriptUnsupportedOperationError(operator.name, value.type(), None, self.compileState)

    def boolean_and(self, tree):
        rest = tree.children

        _conditions = [rest[0]]
        rest = rest[1:]
        while rest:
            _, a, *rest = rest
            _conditions.append(a)

        conditions = []
        for condition in _conditions:
            condition = self.compileState.toResource(
                condition)
            if not isinstance(condition, BooleanResource):
                raise McScriptUnexpectedTypeError("condition", condition.type(), Bool, self.compileState)
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
                raise McScriptUnexpectedTypeError("condition", value.type(), Bool, self.compileState)
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
            raise McScriptUnexpectedTypeError("condition", value.type(), Bool, self.compileState)

        if value.is_static:
            return BooleanResource(not value.static_value, None)

        stack = self.compileState.expressionStack.next()
        self.compileState.ir.append(InvertNode(value.scoreboard_value, stack))
        return BooleanResource(None, stack)

    def binaryOperation(self, *args, assignment_resource: Resource = None):
        number1, *values = args

        # whether the first number may be overwritten
        is_temporary = False
        all_static = all(is_static(i) for i in args[::2])

        # the first number can also be a list. Then just do a binary operation with it
        if isinstance(number1, list):
            number1 = self.binaryOperation(*number1)
            is_temporary = True

        number1 = self.compileState.toResource(number1)

        # by default all operations are in-place. This is not wanted, so the resource is copied
        if isinstance(number1, ValueResource) and not all_static and not is_temporary:
            # copy, except the assign resource is number1 (OPT)
            if assignment_resource is None:
                number1 = number1.copy(self.compileState.expressionStack.next(), self.compileState)

        for i in range(0, len(values), 2):
            operator, number2, = values[i:i + 2]

            if isinstance(number2, list):
                # number2 is now also temporary, but is will not change anyways
                number2 = self.binaryOperation(*number2)

            # get the operator enum type
            operator = BinaryOperator(operator)

            number2 = self.compileState.toResource(number2)

            if not isinstance(number2, ValueResource):
                raise ValueError(
                    "ToDO: Implement boolean operations for non value-resources")

            try:
                number1 = number1.numericOperation(
                    number2, operator, self.compileState)
            except TypeError:
                raise McScriptUnsupportedOperationError(operator.value, number1.type(), number2.type(),
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
            raise McScriptUnsupportedOperationError(operator.name, a.type(), b.type(), self.compileState)

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

        # If the stupid compiler did not manage to put the value onto the last resource, it has to be done now :C
        is_resource_non_static = isinstance(resource, ValueResource) and not resource.is_static
        if is_resource_non_static and isinstance(value, ValueResource) and not value.is_static:
            value = value.copy(resource.scoreboard_value, self.compileState)
        elif resource is None and isinstance(value, ValueResource) and not value.is_static:
            # Form: a = b, where a should be a copy of b, not b itself
            value = value.copy(self.compileState.expressionStack.next(), self.compileState)
        elif is_resource_non_static and isinstance(value, ValueResource) and value.is_static:
            # Form: a = b, where b is a static and a is a nonstatic
            value = value.store(self.compileState, resource.scoreboard_value)
        # Why though
        # # if the variable is new and an atomic value then copy the value
        # if resource is None and isinstance(value, ValueResource):
        #     value = value.copy(self.compileState.expressionStack.next(), self.compileState)

        self.compileState.currentTree = _value
        set_variable(self.compileState, identifier, value)

    def multi_declaration(self, tree):
        *variables, expression = tree.children
        expression = self.compileState.toResource(expression)

        if not isinstance(expression, TupleResource):
            raise McScriptUnexpectedTypeError("Tuple deconstruction", expression.type(), atomic_types.Tuple,
                                              self.compileState)

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
            raise McScriptUnexpectedTypeError("in-place operation", expression, "ValueResource", self.compileState)

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
            raise McScriptUnexpectedTypeError("condition", condition_boolean.type(), Bool, self.compileState)

        if condition_boolean.static_value is not None:
            line_and_column = (block.line, block.column) if condition_boolean else (block_else.line, block_else.column)
            with self.compileState.node_block(ContextType.BLOCK, *line_and_column):
                if condition_boolean.static_value is True:
                    self.visit_children(block)
                elif block_else is not None:
                    self.visit_children(block_else)
                return

        with self.compileState.node_block(ContextType.CONDITIONAL, block.line, block.column) as pos_branch:
            self.visit_children(block)

        if block_else is not None:
            with self.compileState.node_block(ContextType.CONDITIONAL, block_else.line,
                                              block_else.column) as neg_branch:
                self.visit_children(block_else)
        else:
            neg_branch = None

        self.compileState.ir.append(IfNode(
            ConditionalNode([ConditionalNode.IfScoreMatches(
                condition_boolean.scoreboard_value, ScoreRange(0), True)]),
            FunctionCallNode(pos_branch),
            FunctionCallNode(neg_branch) if neg_branch is not None else None
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
            iterator = resource.get_iterator(self.compileState)
        except TypeError:
            raise McScriptUnsupportedOperationError("iteration", resource.type(), None, self.compileState)

        while (value := iterator.next()) is not None:
            with self.compileState.node_block(ContextType.UNROLLED_LOOP, block.line, block.column) as block_function:
                self.compileState.currentContext().add_var(var_name, value)
                self.visit(block)
            self.compileState.ir.append(FunctionCallNode(block_function))

    def return_(self, tree):
        # ToDO: make return an ir node
        resource = self.compileState.toResource(tree.children[0])
        if self.compileState.currentContext().return_resource is not None:
            raise McScriptError("Cannot set the return value twice", self.compileState)
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

        # ToDo: temp
        if function_name == "on_tick":
            if len(parameter_list) > 0:
                raise McScriptArgumentError("The on_tick function takes no arguments", self.compileState)

            with self.compileState.node_block(ContextType.FUNCTION, block.line, block.column, "tick"):
                function.call(self.compileState, [], {})

        self.compileState.currentContext().add_var(function_name, function)

    def function_call(self, tree):
        function_name, *parameters = tree.children
        *accessed_objects, function = get_property(self.compileState, function_name)

        visited_params = [self.visit(i) for i in parameters]

        # any object that implements the call operator can be called. This of course includes function resources.
        try:
            return function.operation_call(self.compileState, *visited_params)
        except TypeError:
            raise McScriptUnexpectedTypeError(str(function), function.type(), "Function", self.compileState)

    def variable_declaration(self, tree):
        identifier, datatype = tree.children
        self.compileState.currentContext().add_var(identifier, TypeResource(
            convert_token_to_type(datatype, self.compileState)
        ))

    def control_struct(self, tree):
        name, block = tree.children
        self.compileState.push_context(
            ContextType.OBJECT, block.line, block.column)
        context = self.compileState.currentContext()

        struct = StructResource(name, context, self.compileState)
        self.compileState.currentContext().add_var(name, struct)

        with self.compileState.new_global_data("struct", struct):
            for declaration in block.children:
                self.visit(declaration)
        self.compileState.pop_context()
        self.compileState.currentContext().add_var(name, struct)

    def context_manipulator(self, tree: Tree):
        *modifiers, block = tree.children

        with self.compileState.node_block(ContextType.CONTEXT_MANIPULATOR, block.line, block.column) as block_function:
            self.visit_children(block)

        self.compileState.ir.append(ExecuteNode(
            readContextManipulator(modifiers, self.compileState),
            [FunctionCallNode(block_function)]
        ))

    def expression(self, tree):
        return self.visit(tree.children[0])

    def statement(self, tree):
        # self.compileState.writeline(f"# {self.compileState.getDebugLines(tree.meta.line, tree.meta.end_line)}")
        res = self.visit_children(tree)
        # # now clear up the expression counter
        # self.compileState.expressionStack.reset()
        return res
