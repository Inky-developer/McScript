import numbers
from typing import Dict

from lark import Transformer, Token, v_args, Tree, Discard
from more_itertools import partition

from src.mcscript.Exceptions import McScriptNameError, McScriptNotImplementError, McScriptTypeError
from src.mcscript.data import defaultEnums
from src.mcscript.lang.Resource.EnumResource import EnumResource
from src.mcscript.lang.Resource.FixedNumberResource import FixedNumberResource
from src.mcscript.lang.Resource.NumberResource import NumberResource
from src.mcscript.lang.Resource.ResourceBase import Resource
from src.mcscript.lang.Resource.ResourceType import ResourceType
from src.mcscript.lang.Resource.SelectorResource import SelectorResource
from src.mcscript.lang.Resource.StringResource import StringResource


class PreCompiler(Transformer):
    """
    Handles static code and optimizations.
    """

    def __init__(self):
        super().__init__(visit_tokens=True)
        # ToDo: match scopes (const vars should not be global vars)
        self.Namespace: Dict[str, Resource] = {}

    def compile(self, tree):
        return self.transform(tree), self.Namespace

    def SELECTOR(self, token):
        return SelectorResource(token, True)

    def STRING(self, token):
        return StringResource(str(token)[1:-1], True)

    def DATATYPE(self, token):
        return Resource.getResourceClass(ResourceType(token.value))

    def signed_value(self, token):
        sign, token = token
        # currently the only sign is minus
        if not isinstance(token, (NumberResource, FixedNumberResource)):
            raise McScriptNotImplementError("Not yet implemented", sign)
        token.setValue(-token.value, True)
        return token

    def value(self, token):
        token, = token
        if isinstance(token, Token):
            if token.type == "NUMBER":
                return NumberResource(int(token), True)
            elif token.type == "DECIMAL":
                return FixedNumberResource.fromNumber(float(token))
            raise McScriptTypeError("Unknown type of value", token)
        elif isinstance(token, numbers.Number):
            return NumberResource(token, True)
        elif isinstance(token, Resource):
            return token
        return self.transform(token)

    @v_args(tree=True)
    def term(self, tree):
        values = tree.children
        if len(values) == 1 and isinstance(values[0], Resource):
            return values[0]
        return tree

    def expression(self, list_):
        return list_[0]

    @v_args(inline=True)
    def property(self, object_, attribute):
        """
        Currently only access to an enum
        :param object_: the enum
        :param attribute: the enum member
        :return: ConstantResource as the number
        """
        if object_ not in self.Namespace:
            if (enum := defaultEnums.get(object_)) is not None:
                # loadToScoreboard the enum into the resources as it is loaded now anyways
                self.Namespace[object_] = enum
                return self.Namespace[object_].getAttribute(attribute)
            raise McScriptNameError(f"Unknown attribute {object_}", object_)
        return self.Namespace[object_].getAttribute(attribute)

    @v_args(inline=True)
    def enum_property(self, token, value=None):
        return token if not value else Tree(None, (token, int(value)))

    @v_args(tree=True)
    def control_enum(self, tree):
        name, block = tree.children
        members = block.children
        keywordProperties, properties = partition(lambda x: isinstance(x, Token), members)
        enum = EnumResource(*properties,
                            **{i.children[0]: NumberResource(i.children[1], True) for i in keywordProperties})
        self.Namespace[name] = enum
        raise Discard

    # @v_args(inline=True)
    # def const_declaration(self, declaration: Tree):
    #     varName, varValue = declaration.children
    #     if not isinstance(varValue, Resource):
    #         raise McScriptNotStaticError("Value is not known at compile-time for constant variable", varValue)
    #     varValue.isStatic = True
    #     self.Namespace[varName] = varValue

    @v_args(tree=True)
    def statement(self, tree):
        if not tree.children:
            raise Discard
        return tree
