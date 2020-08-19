from typing import Dict, Tuple

from lark import Tree, Token
from lark.visitors import Interpreter

from mcscript.analyzer.Analyzer import NamespaceContext
from mcscript.compiler.CompileState import CompileState
from mcscript.compiler.ContextType import ContextType
from mcscript.compiler.common import (conditional_loop, get_property, readContextManipulator, set_property,
                                      declare_variable, update_variable)
from mcscript.compiler.tokenConverter import convert_token_to_resource, convert_token_to_type
from mcscript.data.Config import Config
from mcscript.exceptions.exceptions import (McScriptUnexpectedTypeError, McScriptEnumValueAlreadyDefinedError,
                                            McScriptUnsupportedOperationError, McScriptDeclarationError,
                                            McScriptArgumentError, McScriptIfElseReturnTypeError)
from mcscript.ir.IrMaster import IrMaster
from mcscript.ir.command_components import BinaryOperator, ScoreRelation, UnaryOperator
from mcscript.ir.components import (ConditionalNode, ExecuteNode, FunctionCallNode, StoreFastVarFromResultNode,
                                    StoreFastVarNode, IfNode)
from mcscript.lang import std, atomic_types
from mcscript.lang.atomic_types import Null
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
        return BooleanResource(int(tree.children[0] == "true"), None)

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
                self.compileState.currentTree = child
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
            condition = self.compileState.to_condition(condition)
            static_value = condition.static_value()
            if static_value is not None:
                if static_value:
                    continue
                return BooleanResource(0, None)
            conditions.extend(condition["conditions"])

        if not conditions:
            return BooleanResource(1, None)

        stack = self.compileState.expressionStack.next()

        # None of the conditions will be static
        condition_node = ConditionalNode(conditions)

        if self.compileState.currentContext().user_data.get_is_condition():
            return condition_node

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
            value = self.compileState.to_condition(condition)
            static_value = value.static_value()
            if static_value is not None:
                if static_value:
                    return BooleanResource(1, None)
                # always False boolean does not matter, so it will be discarded
                continue

            conditions.append(value)

        if not conditions:
            return BooleanResource(0, None)

        stack = self.compileState.expressionStack.next()

        # If there are still conditions left, none of them are static
        self.compileState.ir.append(StoreFastVarNode(stack, 0))
        self.compileState.ir.append_all(IfNode(condition, StoreFastVarNode(stack, 1)) for condition in conditions)

        return BooleanResource(None, stack)

    def boolean_not(self, tree):
        _, value = tree.children
        value = self.compileState.to_condition(value)

        static_value = value.static_value()
        if static_value is not None:
            return BooleanResource(int(not static_value), None)

        value.invert()
        if self.compileState.currentContext().user_data.get_is_condition():
            return value

        stack = self.compileState.expressionStack.next()
        self.compileState.ir.append(value)
        return BooleanResource(None, stack)

    def binaryOperation(self, *args, assignment_resource: Resource = None):
        number1, *values = args

        # whether the first number may be overwritten
        is_temporary = isinstance(number1, Resource) and not number1.is_variable
        all_static = all(is_static(i) for i in args[::2])

        # the first number can also be a list. Then just do a binary operation with it
        if isinstance(number1, list):
            number1 = self.binaryOperation(*number1)
            is_temporary = True

        number1 = self.compileState.toResource(number1)

        # by default all operations are in-place. This is not wanted, so the resource is copied
        if isinstance(number1, ValueResource) and (not all_static and not is_temporary) or number1.is_static:
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
            return self.binaryOperation(*self.visit_children(term))
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

        # if currently looking for a condition, return it directly
        if self.compileState.currentContext().user_data.get_is_condition():
            return node

        stack = self.compileState.expressionStack.next()
        self.compileState.ir.append(StoreFastVarFromResultNode(
            stack,
            node
        ))
        return BooleanResource(None, stack)

    def declaration(self, tree):
        identifier, _value = tree.children
        if len(identifier.children) != 1:
            raise McScriptDeclarationError("Cannot declare attributes", self.compileState)

        identifier, = identifier.children

        value = self.compileState.toResource(_value)

        declare_variable(self.compileState, identifier, value)

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
            declare_variable(self.compileState, variable, value)

    def variable_update(self, tree):
        accessor, expression = tree.children

        if len(accessor.children) != 1:
            set_property(self.compileState, accessor, self.visit(expression))

        var_name, = accessor.children

        last_resource = self.compileState.currentContext().find_var(var_name)
        last_resource = last_resource.resource if last_resource is not None else None
        if isinstance(last_resource, ValueResource) and not last_resource.is_static:
            target_resource = last_resource.scoreboard_value
        else:
            target_resource = self.compileState.expressionStack.next()

        with self.compileState.currentContext().set_global_state("declaration", target_resource):
            expression = self.visit(expression)

        update_variable(self.compileState, var_name, expression)

    def operation_ip(self, tree):
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
            BinaryOperator(operator[0]),
            self.compileState
        )

        # store the result back
        set_property(self.compileState, accessor, result)

    def control_if(self, tree):
        # ToDO: This could quite easily turned into an expression
        condition, block, block_else = tree.children

        condition_boolean = self.compileState.to_condition(condition)
        static_value = condition_boolean.static_value()
        if static_value is not None:
            line_and_column = (block.line, block.column) if static_value else (block_else.line, block_else.column)
            with self.compileState.node_block(ContextType.BLOCK, *line_and_column) as function:
                if static_value is True:
                    self.visit_children(block)

                if block_else is not None:
                    self.visit_children(block_else)

                return_value = self.compileState.currentContext().return_resource
            self.compileState.ir.append(FunctionCallNode(function))
            return return_value

        with self.compileState.node_block(ContextType.CONDITIONAL, block.line, block.column) as pos_branch:
            self.visit_children(block)
            pos_branch_resource = self.compileState.currentContext().return_resource

        if block_else is not None:
            with self.compileState.node_block(ContextType.CONDITIONAL, block_else.line,
                                              block_else.column) as neg_branch:
                self.visit_children(block_else)
                neg_branch_resource = self.compileState.currentContext().return_resource
        else:
            neg_branch = None

        self.compileState.ir.append(IfNode(
            condition_boolean,
            FunctionCallNode(pos_branch),
            FunctionCallNode(neg_branch) if neg_branch is not None else None
        ))

        # Handling the return type of an if-else block is difficult.
        # This is how it is handled:
        #   * if condition static, simply return the block resource (see above)
        #   * if no else branch, simply return the pos_branch resource
        #   * if pos_branch_resource static and else_branch_resource not, store pos on else
        #   * also applies the other way around
        #   * if both are static, store both on a new scoreboard value

        if neg_branch is None:
            return pos_branch_resource

        if not isinstance(pos_branch_resource, ValueResource):
            self.compileState.currentTree = block
            raise McScriptIfElseReturnTypeError(pos_branch_resource.type(), self.compileState)

        if not isinstance(neg_branch_resource, ValueResource):
            self.compileState.currentTree = block_else
            raise McScriptIfElseReturnTypeError(neg_branch_resource.type(), self.compileState)

        if not pos_branch_resource.type().matches(neg_branch_resource.type()):
            self.compileState.currentTree = block_else
            raise McScriptUnexpectedTypeError("Else branch", neg_branch_resource.type(), pos_branch_resource.type(),
                                              self.compileState)

        if not pos_branch_resource.is_static:
            target_score = pos_branch_resource.scoreboard_value
        elif not neg_branch_resource.is_static:
            target_score = neg_branch_resource.scoreboard_value
        else:
            target_score = self.compileState.expressionStack.next()

        if pos_branch_resource.scoreboard_value != target_score:
            with self.compileState.ir.with_buffer(pos_branch.inner_nodes):
                pos_branch_resource = pos_branch_resource.copy(target_score, self.compileState)

        if neg_branch_resource != target_score:
            with self.compileState.ir.with_buffer(neg_branch.inner_nodes):
                neg_branch_resource.copy(target_score, self.compileState)

        # Same as neg_branch_resource now
        return pos_branch_resource

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
            self_resource = self.compileState.currentContext().user_data.get_struct()
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
            raise McScriptUnexpectedTypeError(str(function), function.type(), "a function", self.compileState)

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

        with self.compileState.currentContext().set_global_state("struct", struct):
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
        if len(tree.children) == 1 and tree.children[0].data == "expression":
            self.compileState.currentContext().return_resource = res[0]
        return res
