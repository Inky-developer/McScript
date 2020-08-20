import pytest

from tests.tests_full.helper_functions import run_code

EXPECT_PASS = [
    "1 + 2 == 3",
    "1 - 3 == -2",
    "5*6 == 30",
    "15/4 == 3",

    # dyn vars
    "dyn(1) + dyn(2) == 3",
    "1 + dyn(2) == dyn(3)",
    "dyn(1) + 2 == 3",

    "dyn(1) - dyn(2) == -1",
    "1 - dyn(2) == -1",
    "dyn(1) - 2 == -dyn(1)",

    "dyn(2) * dyn(3) == dyn(6)",
    "dyn(2) * 4 == 8",
    "2 * dyn(5) == dyn(10)",

    "dyn(15) / dyn(3) == 5",
    "dyn(25) / 5 == dyn(5)",
    "30 / dyn(10) == dyn(3)",

    # fixed point numbers
    "1.0 + 2.0 == 3.0",
    "1.0 - 3.0 == -2.0",
    "5.0*6.0 == 30.0",
    "15.0/4.0 == 3.75",

    # dyn fixed point numbers
    "dyn(1.0) + dyn(2.0) == 3.0",
    "1.6 + dyn(2.4) == dyn(4.0)",
    "dyn(1.001) + 2.001 == 3.002",

    "dyn(1.0) - dyn(2.0) == -1.0",
    "1.8 - dyn(2.4) == -0.6",
    "dyn(0.99) - 2.001 == -dyn(1.011)",

    "dyn(2.0) * dyn(3.0) == dyn(6.0)",
    "dyn(2.0) * 4.75 == 9.5",
    "2.0 * dyn(5.5) == dyn(11.0)",

    "dyn(15.0) / dyn(3.0) == 5.0",
    "dyn(15.0) / 4.0 == dyn(3.75)",
    "30.0 / dyn(10.5) == dyn(2.857)",

    # functions
    """
    fun test() -> Bool {
        true
    }
    test()
    """,
    """
    fun test_parameter(value: Int) -> Int {
        value * value
    }
    let a = dyn(3)
    test_parameter(a) + a == 12
    """,
    """
    fun test_parameters(a: Int, b: Fixed, c: String, d: Selector) {
        
    }
    test_parameters(1, 2.0, "Test", @e[type=!player])
    true
    """,

    # booleans
    """
    let bool = true
    let bool2 = false
    bool or bool2
    """,
    "not (true and false)",
    "not (not false and false)",
    """
    fun xor(a: Bool, b: Bool) -> Bool {
        a and not b or not a and b
    }
    
    let True = dyn(true)
    let False = dyn(false)
    let static_result = xor(true, false) and xor(false, true) and not xor(true, true) and not xor(false, false)
    let dynamic_result = xor(True, False) and xor(False, True) and not xor(True, True) and not xor(False, False)
    static_result and dynamic_result
    """,

    # if expressions
    """
    let a = 1
    if a == 1 {
        true
    } else {
        false
    }
    """,
    """
    let a = dyn(false)
    if a {
        false
    } else {
        true
    }
    """,
    """
    let a = 1
    let b = dyn(2)
    
    let result = if a == b {
        a
    } else {
        b
    }
    a == dyn(1) and b == 2 and result == 2
    """,
    """
    let a = dyn(1)
    let b = 2
    
    let result = if a == b {
        a + 1
    } else {
        b + 1
    }
    a == 1 and b == dyn(2) and result == 3
    """,
    """
    let a = dyn(1)
    let b = dyn(2)

    let result = if a == b {
        a + 1
    } else {
        b + 1
    }
    a == 1 and b == dyn(2) and result == 3
    """,

    # while loops
    """
    # should be reduced to only true
    while true {}
    true
    """,
    """
    let cond = true
    while cond {
        cond = false
    }
    true
    """,
    """
    let sum = 0
    while sum < 10 {
        sum += 1
    }
    sum == 10
    """,
    """
    let sum = 0
    while sum < 0 {
        sum += 1
    }
    sum == 0
    """,
    """
    let sum = 0
    do {
        sum += 1
    } while sum < 0
    sum == 1
    """

    # enums, currently this is all they can do
    """
    enum MyEnum {
        a,
        b,
        c = 5
    }
    MyEnum.a + MyEnum.b + MyEnum.c == 6
    """,

    # structs
    """
    struct MyStruct {
        Foo: Int
        Bar: Int
        Baz: Int
    }
    
    let m = MyStruct(1, 2, 3)
    m.Foo == 1 and m.Bar == 2 and m.Baz == 3
    """,
    """
    struct A {
        value: Int
    }
    
    struct B {
        value: A
    }
    
    let s = B(A(1))
    
    let first = s.value.value
    s.value.value = 2
    
    first == 1 and s.value.value == 2
    """,
    """
    struct Complex {
        real: Fixed
        imag: Fixed
        
        fun add(self, other: Complex) -> Complex {
            Complex(self.real + other.real, self.imag + other.imag)
        }
        
        fun square(self) -> Fixed {
            self.real*self.real + self.imag*self.imag
        }
    }
    
    let c1 = Complex(1.5, 2.5)
    let c2 = Complex(-5.0, 2.0)
    
    let sum = c1.add(c2)
    
    let square = c2.square()
    let con = sum.real==-3.5 and sum.imag==4.5 and c1.real==1.5 and c2.real==-5.0 and c1.imag==2.5 and c2.imag==2.0
    square == 29.0 and con 
    """,
    """
    struct Range {
        min: Int
        max: Int
        current: Int
        
        fun new(min: Int, max: Int) -> Range {
            Range(min, max-1, min-1)
        }
        
        fun next(self) -> Tuple {
            self.current += 1
            (self.current, self.current < self.max)
        }
    }
    
    let r = Range.new(0, 10)
    let sum = 0
    do {
        let (value, not_empty) = r.next()
        sum += value
    } while not_empty
    
    sum == 45
    """

]


@pytest.mark.parametrize("code", EXPECT_PASS)
def test_mcscript(rcon, test_world, code):
    result = run_code(rcon, test_world, code)
    print(result)
    result_val, message = result
    if result_val is None or result_val == 0:
        pytest.fail(f"Returned {result_val}, {message}")
