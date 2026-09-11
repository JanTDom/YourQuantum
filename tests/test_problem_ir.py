"""Tests for ProblemIR domain model and expression evaluator."""
import pytest
from backend.domain.problem_ir import (
    Constraint, ConstraintType, ExprNode, ExpressionRegistry,
    MissingInfo, MissingInfoImpact, Objective, ObjectiveDirection,
    ProblemIR, Variable, VariableDomain, ComputeBudget,
)
from backend.domain.evaluator import ExpressionEvaluator, EvaluationError


def make_simple_ir(approved: bool = True) -> ProblemIR:
    reg = ExpressionRegistry()
    reg.add(ExprNode(id="vx", op="var", value="x"))
    reg.add(ExprNode(id="vy", op="var", value="y"))
    reg.add(ExprNode(id="sum_xy", op="sum", children=["vx", "vy"]))
    reg.add(ExprNode(id="const2", op="const", value=2.0))
    from datetime import datetime, timezone
    return ProblemIR(
        description_raw="test",
        description_formalised="test",
        variables=[
            Variable(id="x", name="x", domain=VariableDomain.BINARY),
            Variable(id="y", name="y", domain=VariableDomain.BINARY),
        ],
        expressions=reg,
        objectives=[Objective(id="obj", direction=ObjectiveDirection.MINIMIZE, expression_id="sum_xy")],
        constraints=[
            Constraint(id="c0", type=ConstraintType.EQUALITY,
                       lhs_expression_id="sum_xy", rhs_expression_id="const2", hard=True)
        ],
        approved=approved,
        approved_at=datetime.now(timezone.utc) if approved else None,
    )


def test_problem_ir_fields():
    ir = make_simple_ir()
    assert ir.is_ready_to_solve
    assert len(ir.variables) == 2
    assert len(ir.constraints) == 1
    assert len(ir.objectives) == 1


def test_problem_ir_not_ready_when_not_approved():
    ir = make_simple_ir(approved=False)
    assert not ir.is_ready_to_solve


def test_missing_info_blocking():
    ir = make_simple_ir()
    ir.missing_information.append(
        MissingInfo(id="m0", description="missing", impact=MissingInfoImpact.BLOCKS_SOLVING,
                    clarification_question="?")
    )
    assert not ir.is_ready_to_solve


def test_variable_by_id():
    ir = make_simple_ir()
    v = ir.variable_by_id("x")
    assert v is not None and v.name == "x"
    assert ir.variable_by_id("nonexistent") is None


class TestEvaluator:
    def make_evaluator(self):
        reg = ExpressionRegistry()
        reg.add(ExprNode(id="va", op="var", value="a"))
        reg.add(ExprNode(id="vb", op="var", value="b"))
        reg.add(ExprNode(id="c5", op="const", value=5.0))
        reg.add(ExprNode(id="c2", op="const", value=2.0))
        reg.add(ExprNode(id="add_ab", op="add", children=["va", "vb"]))
        reg.add(ExprNode(id="mul_ab", op="mul", children=["va", "vb"]))
        reg.add(ExprNode(id="sub_ab", op="sub", children=["va", "vb"]))
        reg.add(ExprNode(id="sum3", op="sum", children=["va", "vb", "c5"]))
        reg.add(ExprNode(id="le_ab", op="le", children=["va", "vb"]))
        reg.add(ExprNode(id="neg_a", op="neg", children=["va"]))
        return ExpressionEvaluator(reg), reg

    def test_const(self):
        ev, reg = self.make_evaluator()
        assert ev.evaluate("c5", {}) == 5.0

    def test_var(self):
        ev, _ = self.make_evaluator()
        assert ev.evaluate("va", {"a": 3}) == 3.0

    def test_add(self):
        ev, _ = self.make_evaluator()
        assert ev.evaluate("add_ab", {"a": 3, "b": 2}) == 5.0

    def test_mul(self):
        ev, _ = self.make_evaluator()
        assert ev.evaluate("mul_ab", {"a": 4, "b": 3}) == 12.0

    def test_sub(self):
        ev, _ = self.make_evaluator()
        assert ev.evaluate("sub_ab", {"a": 5, "b": 3}) == 2.0

    def test_sum(self):
        ev, _ = self.make_evaluator()
        assert ev.evaluate("sum3", {"a": 1, "b": 2}) == 8.0  # 1+2+5

    def test_le_true(self):
        ev, _ = self.make_evaluator()
        assert ev.evaluate("le_ab", {"a": 1, "b": 2}) == 1.0

    def test_le_false(self):
        ev, _ = self.make_evaluator()
        assert ev.evaluate("le_ab", {"a": 3, "b": 2}) == 0.0

    def test_neg(self):
        ev, _ = self.make_evaluator()
        assert ev.evaluate("neg_a", {"a": 7}) == -7.0

    def test_missing_var_raises(self):
        ev, _ = self.make_evaluator()
        with pytest.raises(EvaluationError):
            ev.evaluate("va", {})

    def test_unknown_node_raises(self):
        ev, _ = self.make_evaluator()
        with pytest.raises(EvaluationError):
            ev.evaluate("nonexistent_node_id", {"a": 1})
