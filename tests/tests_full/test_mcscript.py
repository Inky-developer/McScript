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
    """
]


@pytest.mark.parametrize("code", EXPECT_PASS)
def test_mcscript(rcon, test_world, code):
    result = run_code(rcon, test_world, code)
    print(result)
    result_val, message = result
    if result_val is None or result_val == 0:
        pytest.fail(f"Returned {result_val}, {message}")
