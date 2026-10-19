import pytest

from tools.calculator import SafeCalculator


@pytest.fixture
def calculator():
    return SafeCalculator()


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("10 + 5", 15),
        ("6 * 7", 42),
        ("2 ** 5", 32),
        ("10 / 2", 5),
        ("17 // 3", 5),
        ("17 % 3", 2),
        ("-(4 + 3)", -7),
        ("2 ** -2", 0.25),
    ],
)
def test_valid_expressions(calculator, expression, expected):
    assert calculator.calculate(expression) == expected


@pytest.mark.parametrize(
    "expression",
    [
        "",
        " ",
        "10 / 0",
        "2 ** 101",
        "abc",
        "__import__('os').system('echo unsafe')",
        "2 + True",
    ],
)
def test_invalid_expressions(calculator, expression):
    with pytest.raises((ValueError, TypeError)):
        calculator.calculate(expression)


def test_expression_length_limit():
    calculator = SafeCalculator(max_expression_length=5)

    with pytest.raises(ValueError):
        calculator.calculate("123456")


def test_boolean_result_is_rejected(calculator):
    with pytest.raises(ValueError):
        calculator.calculate("True")