import unittest

from mcscript.Exceptions.compileExceptions import McScriptArgumentsError
from mcscript.compiler.CompileState import CompileState
from mcscript.data import Config
from mcscript.lang.builtins.GetBlockFunction import GetBlockFunction
from mcscript.lang.builtins.SetBlockFunction import SetBlockFunction
from mcscript.lang.builtins.StringFormatFunction import StringFormatFunction
from mcscript.lang.builtins.textFunctions import PrintFunction
from mcscript.lang.resource.NumberResource import NumberResource
from mcscript.lang.resource.StringResource import StringResource
from mcscript.lang.resource.TypeResource import TypeResource
from mcscript.lang.resource.base.functionSignature import FunctionParameter, FunctionSignature


class TestFunctionSignature(unittest.TestCase):
    def setUp(self) -> None:
        self.compileState = CompileState("Example code", [], lambda x: x, Config())

        self.signature1 = FunctionSignature(
            StringFormatFunction(),
            [
                FunctionParameter(
                    "text",
                    TypeResource(StringResource),
                    FunctionParameter.ParameterCount.ONCE,
                    accepts=FunctionParameter.ResourceMode.STATIC
                ),
                FunctionParameter(
                    "format_strings",
                    TypeResource(StringResource),
                    FunctionParameter.ParameterCount.ARBITRARY,
                    accepts=FunctionParameter.ResourceMode.STATIC
                )
            ],
            TypeResource(StringResource)
        )

        self.signature2 = FunctionSignature(
            SetBlockFunction(),
            [
                FunctionParameter(
                    "block",
                    TypeResource(NumberResource),
                    FunctionParameter.ParameterCount.ONCE
                ),
                FunctionParameter(
                    "x",
                    TypeResource(NumberResource),
                    FunctionParameter.ParameterCount.ONCE,
                    NumberResource(0, True)
                ),
                FunctionParameter(
                    "y",
                    TypeResource(NumberResource),
                    FunctionParameter.ParameterCount.ONCE,
                    NumberResource(0, True)
                ),
                FunctionParameter(
                    "z",
                    TypeResource(NumberResource),
                    FunctionParameter.ParameterCount.ONCE,
                    NumberResource(0, True)
                )
            ],
            TypeResource(StringResource)
        )

        self.signature3 = FunctionSignature(
            PrintFunction(),
            [
                FunctionParameter(
                    "text",
                    TypeResource(StringResource),
                    FunctionParameter.ParameterCount.ONE_OR_MORE
                )
            ],
            TypeResource(StringResource)
        )

    def testSignatureSuccess(self):
        parameters = [StringResource("Hello, $!", True), StringResource("World", True), StringResource("spam", True)]
        parameters = self.signature1.matchParameters(self.compileState, parameters)
        print(parameters)
        self.assertEqual(len(parameters), 3)

        parameters = [NumberResource(1, True), NumberResource(0, True), NumberResource(10, True)]
        parameters = self.signature2.matchParameters(self.compileState, parameters)
        print(parameters)
        self.assertEqual(len(parameters), 4)

    def testSignatureFailure(self):
        parameters = [NumberResource(1, True)]
        self.assertRaisesRegex(
            McScriptArgumentsError,
            r"Expected type .+ for parameter '.+' but got type .+",
            self.signature1.matchParameters,
            self.compileState, parameters
        )

        parameters = [StringResource("Hello, $!", True), StringResource("World", True), NumberResource(1, True)]
        self.assertRaisesRegex(
            McScriptArgumentsError,
            r"All parameters for '.+' must be of type .+ but got (.+)",
            self.signature1.matchParameters,
            self.compileState, parameters
        )

        parameters = []
        self.assertRaisesRegex(
            McScriptArgumentsError,
            r"Expected parameter '.+' but got nothing",
            self.signature3.matchParameters,
            self.compileState, parameters
        )

        self.assertRaisesRegex(
            McScriptArgumentsError,
            r"Parameter .+ must be static but got (.+)",
            self.signature1.matchParameters,
            self.compileState, [StringResource("static", False, 5)]
        )

    def testFunction(self):
        function = GetBlockFunction()
        signature = function.getFunctionSignature
        print(signature)
