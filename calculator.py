#!/usr/bin/env python3

import ast
import operator as op
import sys
from typing import Any


# Разрешённые операции
BINARY_OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
}

UNARY_OPERATORS = {
    ast.UAdd: op.pos,
    ast.USub: op.neg,
}


class SafeEvaluator(ast.NodeVisitor):
    """Безопасный вычислитель арифметических выражений на базе AST."""

    def visit_Expression(self, node: ast.Expression) -> Any:
        return self.visit(node.body)

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        left = self.visit(node.left)
        right = self.visit(node.right)
        operator_type = type(node.op)
        if operator_type in BINARY_OPERATORS:
            try:
                return BINARY_OPERATORS[operator_type](left, right)
            except ZeroDivisionError:
                raise ValueError("Деление на ноль недопустимо")
        raise ValueError(f"Недопустимая бинарная операция: {operator_type.__name__}")

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        operand = self.visit(node.operand)
        operator_type = type(node.op)
        if operator_type in UNARY_OPERATORS:
            return UNARY_OPERATORS[operator_type](operand)
        raise ValueError(f"Недопустимая унарная операция: {operator_type.__name__}")

    def visit_Constant(self, node: ast.Constant) -> Any:
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Разрешены только числовые литералы")

    # Совместимость со старыми версиями Python (<3.8)
    def visit_Num(self, node: ast.Num) -> Any:  # type: ignore[override]
        return node.n

    # Запрещаем имена, атрибуты, вызовы функций и т.д.
    def visit_Name(self, node: ast.Name) -> Any:  # noqa: N802
        raise ValueError("Имена/переменные не разрешены")

    def visit_Call(self, node: ast.Call) -> Any:
        raise ValueError("Вызовы функций не разрешены")

    def generic_visit(self, node: ast.AST) -> Any:
        allowed_nodes = (
            ast.Expression,
            ast.BinOp,
            ast.UnaryOp,
            ast.Constant,
            ast.Num,  # для старых версий Python
            ast.Load,
            ast.Add,
            ast.Sub,
            ast.Mult,
            ast.Div,
            ast.FloorDiv,
            ast.Mod,
            ast.Pow,
            ast.UAdd,
            ast.USub,
            ast.Expr,
        )
        if not isinstance(node, allowed_nodes):
            raise ValueError(f"Недопустимая конструкция: {type(node).__name__}")
        return super().generic_visit(node)


def preprocess_expression(expression: str) -> str:
    """
    Подготовить строку выражения перед парсингом.
    - Заменяем ^ на ** (более привычно для калькуляторов: степень)
    - Обрезаем пробелы по краям
    """
    return expression.replace("^", "**").strip()


def evaluate_expression(expression: str) -> Any:
    """Безопасно вычисляет арифметическое выражение."""
    prepared = preprocess_expression(expression)
    try:
        parsed = ast.parse(prepared, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Синтаксическая ошибка: {exc.msg}") from exc
    evaluator = SafeEvaluator()
    return evaluator.visit(parsed)


def repl() -> None:
    print("Интерактивный калькулятор. Введите выражение (или 'exit'/'quit' для выхода).")
    while True:
        try:
            line = input("calc> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line.lower() in {"exit", "quit"}:
            break
        try:
            result = evaluate_expression(line)
            print(result)
        except Exception as exc:  # noqa: BLE001
            print(f"Ошибка: {exc}")


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        # Аргументом передано выражение
        expr = " ".join(argv[1:])
        try:
            result = evaluate_expression(expr)
            print(result)
            return 0
        except Exception as exc:  # noqa: BLE001
            print(f"Ошибка: {exc}", file=sys.stderr)
            return 1
    # Иначе запускаем REPL
    repl()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv)) 