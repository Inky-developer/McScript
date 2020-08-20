from contextlib import suppress

import pytest

from mcscript.compile import compileMcScript
from mcscript.data.Config import Config
from mcscript.exceptions.McScriptException import McScriptError
from mcscript.exceptions.exceptions import (McScriptUndefinedVariableError, McScriptUndefinedAttributeError,
                                            McScriptUnexpectedTypeError, McScriptEnumValueAlreadyDefinedError,
                                            McScriptUnsupportedOperationError, McScriptDeclarationError,
                                            McScriptIfElseReturnTypeError, McScriptArgumentError, McScriptValueError,
                                            McScriptInvalidSelectorError, McScriptInlineRecursionError,
                                            McScriptOutOfBoundsError, McScriptInvalidMarkupError)

EXPECT_FAIL = [
    (
        "a",
        McScriptUndefinedVariableError
    ),
    (
        "let b = 1\na",
        McScriptUndefinedVariableError
    ),
    (
        """
        struct Foo {}
        
        let f = Foo()
        f.x
        """,
        McScriptUndefinedAttributeError
    ),
    (
        """
        let a = 1
        a = true
        """,
        McScriptUnexpectedTypeError
    ),
    (
        """
        struct Foo {
            bar: Int
        }
        
        let f = Foo(true)
        """,
        McScriptUnexpectedTypeError
    ),
    (
        """
        struct Foo {
            bar: Int
        }
        
        let f = Foo(1)
        f.bar = true
        """,
        McScriptUnexpectedTypeError
    ),
    (
        "run anchored 'somewhere' {}",
        McScriptError
    ),
    (
        "run for 1 {}",
        McScriptUnexpectedTypeError
    ),
    (
        "run at 1 {}",
        McScriptUnexpectedTypeError
    ),
    (
        """
        enum Foo {
            a,
            a
        }
        """,
        McScriptEnumValueAlreadyDefinedError
    ),
    (
        """
        enum Foo {
            a,
            a = 10
        }
        """,
        McScriptEnumValueAlreadyDefinedError
    ),
    (
        """
        enum Foo {a}
        Foo.a
        """,
        McScriptUndefinedAttributeError
    ),
    (
        """
        let a = 1
        a[0]
        """,
        McScriptUnsupportedOperationError
    ),
    (
        """
        let a = 1
        a[0] = 2
        """,
        McScriptUnsupportedOperationError
    ),
    (
        """
        let a = "Test"
        -a
        """,
        McScriptUnsupportedOperationError
    ),
    (
        """
        struct Foo {}
        
        let f = Foo()
        f + 2
        """,
        McScriptUnsupportedOperationError
    ),
    (
        """
        let a.b = 3
        """,
        McScriptDeclarationError
    ),
    (
        "let (a, b, c) = 1",
        McScriptUnexpectedTypeError
    ),
    (
        "let (a, b, c) = (1, 2)",
        McScriptDeclarationError
    ),
    (
        "let (a, b) = (1, 2, 3)",
        McScriptDeclarationError
    ),
    (
        """
        let a = 1
        a += "Test"
        """,
        McScriptUnexpectedTypeError
    ),
    (
        "if true { 'test' }",
        McScriptIfElseReturnTypeError
    ),
    (
        "if false { 1 } else { 'test' }",
        McScriptIfElseReturnTypeError
    ),
    (
        "if dyn(true) { 1 } else { 1.0 }",
        McScriptUnexpectedTypeError
    ),
    (
        "for i in 10 {}",
        McScriptUnsupportedOperationError
    ),
    (
        "fun test(self) {}",
        McScriptDeclarationError
    ),
    (
        "fun on_tick(ticks: Int) {}",
        McScriptArgumentError
    ),
    (
        """
        let a = 1
        a()
        """,
        McScriptUnexpectedTypeError
    ),
    (
        """
        fun fail(a: NotExistent) {}
        """,
        McScriptValueError
    ),
    (
        "@p[type=armor_stand]",
        McScriptInvalidSelectorError
    ),
    (
        "@e[type=armor_stand,type=armor_stand]",
        McScriptInvalidSelectorError
    ),
    (
        "@e[gamemode=creative,gamemode=survival]",
        McScriptInvalidSelectorError
    ),
    (
        "@e[gamemode=lalalalala]",
        McScriptInvalidSelectorError
    ),
    (
        "@e[lalalalala=lalalalala]",
        McScriptInvalidSelectorError
    ),
    (
        """
        fun is_even(number: Int) -> Bool {
            not is_odd(number)
        }
        
        fun is_odd(number: Int) -> Bool {
            not is_even(number)
        }
        """,
        McScriptInlineRecursionError
    ),
    (
        """
        struct Foo {
            a: Int
        }
        
        Foo(true)
        """,
        McScriptUnexpectedTypeError
    ),
    (
        """
        struct Foo {
            a: Int
        }
        
        Foo(1, 1)
        """,
        McScriptArgumentError
    ),
    (
        """
        struct Foo {}
        let f = Foo()
        f.a = 1
        """,
        McScriptUndefinedAttributeError
    ),
    (
        """
        struct Foo {
            a: Int
        }
        
        let f = Foo(1)
        f.a = true
        """,
        McScriptUnexpectedTypeError
    ),
    (
        """
        let a = (1, 2, 3)
        a[3]
        """,
        McScriptOutOfBoundsError
    ),
    (
        """
        let a = (1, 2, 3)
        a["Hallo"]
        """,
        McScriptUnexpectedTypeError
    ),
    (
        """
        print("{}{}", 1)
        """,
        McScriptArgumentError
    ),
    (
        """
        print("{}", 1, 2)
        """,
        McScriptArgumentError
    ),
    (
        "print('[regex]test[/]')",
        McScriptInvalidMarkupError
    )

]


@pytest.mark.parametrize("code, exception", EXPECT_FAIL)
def test_mcscript(code, exception):
    config = Config()
    config.input_string = code

    try:
        with suppress(exception):
            compileMcScript(config)
    except Exception as e:
        pytest.fail(f"Expected {exception} but failed with: {type(e)}")
