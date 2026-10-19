import ast
import math
import operator


class SafeCalculator:
    """Evaluate basic arithmetic without executing arbitrary Python code."""

    _binary_operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
    }

    _unary_operators = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
    }

    def __init__(self, max_expression_length: int = 200) -> None:
        if max_expression_length < 1:
            raise ValueError("Maximum expression length must be positive.")

        self.max_expression_length = max_expression_length

    def calculate(self, expression: str) -> int | float:
        """Calculate a supported arithmetic expression."""

        if not isinstance(expression, str) or not expression.strip():
            raise ValueError("Expression cannot be empty.")

        if len(expression) > self.max_expression_length:
            raise ValueError("Expression is too long.")

        try:
            tree = ast.parse(expression, mode="eval")
            result = self._evaluate(tree.body)
        except (SyntaxError, ZeroDivisionError, OverflowError) as exc:
            raise ValueError("Invalid or unsafe arithmetic expression.") from exc

        if isinstance(result, bool) or not isinstance(result, (int, float)):
            raise ValueError("Expression did not produce a valid number.")

        if not math.isfinite(result):
            raise ValueError("Result must be finite.")

        if abs(result) > 1e100:
            raise ValueError("Result exceeds the permitted limit.")

        return result

    def _evaluate(self, node: ast.AST) -> int | float:
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool) or not isinstance(
                node.value, (int, float)
            ):
                raise ValueError("Only numeric constants are supported.")

            if abs(node.value) > 1e100:
                raise ValueError("Number exceeds the permitted limit.")

            return node.value

        if isinstance(node, ast.BinOp):
            operation = self._binary_operators.get(type(node.op))

            if operation is None:
                raise ValueError("Operator is not supported.")

            left = self._evaluate(node.left)
            right = self._evaluate(node.right)

            if isinstance(node.op, ast.Pow):
                if abs(right) > 100:
                    raise ValueError("Exponent exceeds the permitted limit.")

            result = operation(left, right)

            if isinstance(result, float) and not math.isfinite(result):
                raise ValueError("Result must be finite.")

            if abs(result) > 1e100:
                raise ValueError("Result exceeds the permitted limit.")

            return result

        if isinstance(node, ast.UnaryOp):
            operation = self._unary_operators.get(type(node.op))

            if operation is None:
                raise ValueError("Unary operator is not supported.")

            return operation(self._evaluate(node.operand))

        raise ValueError("Expression contains an unsupported operation.")