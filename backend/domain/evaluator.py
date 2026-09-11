"""
YourQuantum — Safe Expression Evaluator
Evaluates ExprNode trees without eval/exec.
All variable values must be supplied as a dict.
"""
from __future__ import annotations

import math
from typing import Any

from backend.domain.problem_ir import ExpressionRegistry, ExprNode


class EvaluationError(Exception):
    pass


class ExpressionEvaluator:
    """
    Evaluates an expression tree given a variable assignment.
    Raises EvaluationError on type mismatch or unknown operator.
    Never calls eval(), exec(), or compile().
    """

    BINARY_OPS = {
        "add": lambda a, b: a + b,
        "sub": lambda a, b: a - b,
        "mul": lambda a, b: a * b,
        "div": lambda a, b: a / b if b != 0 else math.nan,
        "eq":  lambda a, b: float(a == b),
        "le":  lambda a, b: float(a <= b),
        "ge":  lambda a, b: float(a >= b),
        "lt":  lambda a, b: float(a < b),
        "gt":  lambda a, b: float(a > b),
        "ne":  lambda a, b: float(a != b),
        "and_": lambda a, b: float(bool(a) and bool(b)),
        "or_":  lambda a, b: float(bool(a) or bool(b)),
    }

    def __init__(self, registry: ExpressionRegistry):
        self._reg = registry

    def evaluate(self, node_id: str, assignment: dict[str, Any]) -> float:
        """
        Evaluate the expression rooted at node_id with the given variable
        assignment (variable_id → numeric value).
        Returns a finite float. Boolean results are 1.0 (true) or 0.0 (false).
        Raises EvaluationError if expression produces NaN, inf, or on error.
        """
        node = self._reg.nodes.get(node_id)
        if node is None:
            raise EvaluationError(f"Unknown expression node: {node_id!r}")
        val = self._eval_node(node, assignment)
        if math.isnan(val) or math.isinf(val):
            raise EvaluationError(f"Expression {node_id!r} evaluated to non-finite value: {val}")
        return val

    def _eval_node(self, node: ExprNode, assignment: dict[str, Any]) -> float:
        op = node.op

        if op == "const":
            return float(node.value)  # type: ignore[arg-type]

        if op == "var":
            vid = node.value
            if vid not in assignment:
                raise EvaluationError(
                    f"Variable {vid!r} not found in assignment. "
                    f"Available: {list(assignment)}"
                )
            return float(assignment[vid])

        if op == "neg":
            child = self._eval_child(node, 0, assignment)
            return -child

        if op == "not_":
            child = self._eval_child(node, 0, assignment)
            return float(not bool(child))

        if op in self.BINARY_OPS:
            a = self._eval_child(node, 0, assignment)
            b = self._eval_child(node, 1, assignment)
            return self.BINARY_OPS[op](a, b)

        if op == "min":
            vals = [self._eval_child(node, i, assignment)
                    for i in range(len(node.children))]
            return min(vals)

        if op == "max":
            vals = [self._eval_child(node, i, assignment)
                    for i in range(len(node.children))]
            return max(vals)

        if op == "sum":
            return sum(
                self._eval_child(node, i, assignment)
                for i in range(len(node.children))
            )

        if op == "if_":
            # if_(condition, then, else)
            cond = self._eval_child(node, 0, assignment)
            return (
                self._eval_child(node, 1, assignment)
                if bool(cond)
                else self._eval_child(node, 2, assignment)
            )

        raise EvaluationError(f"Unknown operator: {op!r}")

    def _eval_child(
        self, node: ExprNode, idx: int, assignment: dict[str, Any]
    ) -> float:
        if idx >= len(node.children):
            raise EvaluationError(
                f"Operator {node.op!r} expected child at index {idx}, "
                f"but only {len(node.children)} children present."
            )
        child_id = node.children[idx]
        child = self._reg.nodes.get(child_id)
        if child is None:
            raise EvaluationError(
                f"Child node {child_id!r} not found in registry."
            )
        return self._eval_node(child, assignment)
