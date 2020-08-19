import pytest
from lark.exceptions import LarkError

from mcscript import get_grammar

EXPECT_PASS = [
    """
    
    """,
    "",

    # expressions
    "1",
    "1.2",
    "1.2232132112321",
    ".1",
    '"A String with unicode ±"',
    "'A single quoted string'",
    "true",
    "false",
    '("a", "tuple", 1,1.2,.2)',
    '-15',
    'variable',
    'object.sub.variable',
    'array[0]',
    'array[5 + 6]',
    'function(1, 2, 3, "String", (1, 2,3),)',
    """
    function.over.multiple.lines(
    1,
            2,
                if function() {
                    17
                },
    )
    """
    'object.sub.method(1, variable, if 1+1 {1} else {0})',
    'if variable {8} else {5}',
    '"value" + "value"',
    '1 + 1',
    '15 * 9',
    '16-1516516515',
    '1/8',
    '(5 + 6*x) * (x*x)',
    '(5 + 6*x) * (x*x) == 1',
    '(a) == b',
    'b > a',
    'b >= a',
    'b != if a {1} else {0}',
    'b<-500000',
    'b<=10',
    'a and b or not c',

    # declarations
    'let a = b',
    'let b = (1, 2, 3, 4)',
    'let j.d = j.d()',
    'let (a, b, c, d) = 1',
    'let (a, b, c, d) = (1, 2, 3, 4)',
    'a = (1, 2, 3, 4)',
    'a=a==a',
    'a=a[0]',
    'a[a]=a[a]+a',
    'x += x + x',
    'y *= 1',
    'z -= 16',
    'z /= 18',
    'z %= 18',

    # function definitions
    'fun a(value: type, value2: type) {}',
    'fun a() -> result {}',
    'fun a(self) -> Type {}',
    'fun a(self, Int: Int, String: String) -> Self {}',
    """
    fun with_newlines() {
    
        print("Newline, above!")
    }
    """

    # control flow
    'while 1 {}',
    'while if 1 {1} else {2} {}',
    'while (a > b) {}',
    'while steps < 15 and not hit at @s {}',
    'do absolute 1, 2, 3{}while 1',
    'for variable in 1 {}',
    'for x in if 10 {range(10)} {}',

    # enums and structs
    'enum enum {a,b,c,d=10,e=100}',
    """
    enum E {
        a,b,
    c,d=100,
    
    f=10
    }
    """,
    """
    struct struct {
        a: a
        b: b
        
        # comment
        
        Int: Int
    }
    """,
    """
    # a comment
    struct A {
        # another comment
        fun a_function(a: Int, b: b) {}
        fun a_method(self, Int: Int) {}
    }
    """,

    # context
    'run for @a {}',
    'run at @s {}',
    'run absolute 1, 2, 3 {}',
    'run local 1, 2, 3 {}',
    'run relative 10,"20",30 {}',
    'run      absolute 10.2,1,1 {} ',
    ' run anchored "eyes" {}',
    'run anchored "feet" {}',
]

# noinspection SpellCheckingInspection
EXPECT_FAIL = [
    """
    ,
    """,
    "!",

    # expressions
    "1+",
    "1.2-",
    "+1.2232132112321",
    ".",
    """"A String with different quotes'""",
    '("a", "tuple", 1,1.2,.2))',
    '+-15',
    'variable.',
    'object.sub.',
    'array[]',
    'function(1, 2, 3, "String", (1, 2,3),,)',
    'object.sub.method(1 variable, if 1+1 {1} else {0})',
    'if variable',
    '1 + 1 +',
    '15 * 9 *',
    '16-1516516515-',
    '1//8',
    '(a) == == b',
    'b >> a',
    '>= a',
    'a and b or or not c',
    'a and and b',
    'aand b'

    # declarations
    'leta = b',
    'let b == (1, 2, 3, 4)',
    'let j. = j.d()',
    'let a, b, c, d) = 1',
    '.a = (1, 2, 3, 4)',
    'a==a==a',
    'let a[a]=a[a]+a',
    'x += + x + x',

    # function definitions
    'funa(value: type, value2: type) {}',
    'fun a() -> result',
    'fun a(self, self) -> Type {}',
    'fun a(self Int: Int, String: String, self) -> Self {}',

    # control flow
    'while1 {}',
    'while if 1 {1}',
    'while (a > b {})',
    'while steps < 15 and not hit at @s as @a {}',
    'doabsolute 1, 2, 3{}while 1',
    'for variablein 1 {}',
    'forx in if 10 {range(10)} {}',

    # enums and structs
    'enum enum {a,b,c,d=10,e=100,d=10.5}',
    """
    enum E {
        a,b
    c,d=100,
    
    f=10
    }
    """,
    """
    structstruct {
        a: a
        b: b
    }
    """,
    """
    # a comment
    struct A {
        # another comment
        fun a_function(a: 
            Int, b: b) {}
        fun a_method(self, Int: :Int) {}
    }
    """,

    # context
    'run for@a {}',
    'run at @o {}',
    'run absolute 1, 2, 3, 4 {}',
    'run local 1, 2, {}',
    'run relative "10,20,30" {}'
]


@pytest.mark.parametrize("sample", EXPECT_PASS)
def test_pass(sample):
    try:
        get_grammar().parse(sample)
    except LarkError:
        pytest.fail(f"Failed to parse")


@pytest.mark.parametrize("sample", EXPECT_FAIL)
def test_fail(sample):
    try:
        get_grammar().parse(sample)
    except LarkError:
        return True
    pytest.fail(f"Successfully parsed code that should fail")
