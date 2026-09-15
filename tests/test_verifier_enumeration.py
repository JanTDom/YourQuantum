"""
Tests for independent verifier small-N enumeration threshold (V9-A).
"""

from datetime import datetime, timezone
import pytest

from backend.domain.problem_ir import (
    Constraint,
    ConstraintType,
    ExprNode,
    ExpressionRegistry,
    Objective,
    ObjectiveDirection,
    ProblemIR,
    Variable,
    VariableDomain,
)
from backend.verifier.verifier import (
    IndependentVerifier,
    MAX_ENUMERATION_VARS,
    SolverCandidate,
    Verdict,
)


def create_binary_problem_with_lp_gap(n: int) -> ProblemIR:
    """
    Tworzy zadanie optymalizacji binarnej o n zmiennych z gwarantowaną luką relaksacji LP:
    min sum_{i=0}^{n-1} x_i
    p.o. sum_{i=0}^{n-1} x_i >= 1.5
    Dla relaksacji ciągłej (LP): x_0=1, x_1=0.5 -> obj = 1.5.
    Dla całkowitoliczbowego (IP): min sum = 2.0 (luka LP = (2.0 - 1.5)/2.0 = 25%).
    """
    reg = ExpressionRegistry()
    variables = []
    var_node_ids = []

    for i in range(n):
        vid = f"x_{i}"
        variables.append(Variable(id=vid, name=vid, domain=VariableDomain.BINARY))
        reg.add(ExprNode(id=f"v_{vid}", op="var", value=vid))
        var_node_ids.append(f"v_{vid}")

    # Sum of all variables
    reg.add(ExprNode(id="sum_all", op="sum", children=var_node_ids))
    reg.add(ExprNode(id="rhs_1_5", op="const", value=1.5))

    return ProblemIR(
        id=f"gap_prob_{n}",
        description_raw=f"Binary problem with LP gap n={n}",
        description_formalised=f"Binary problem with LP gap n={n}",
        variables=variables,
        expressions=reg,
        objectives=[
            Objective(
                id="min_sum",
                direction=ObjectiveDirection.MINIMIZE,
                expression_id="sum_all",
            )
        ],
        constraints=[
            Constraint(
                id="c_ge_1_5",
                type=ConstraintType.INEQUALITY_GE,
                lhs_expression_id="sum_all",
                rhs_expression_id="rhs_1_5",
                hard=True,
            )
        ],
        approved=True,
        approved_at=datetime.now(timezone.utc),
    )


def test_enumeration_certifies_optimality_at_threshold():
    """
    Zadanie binarne o n = MAX_ENUMERATION_VARS z luką LP otrzymuje optimality_proven: True
    dzięki niezależnej enumeracji.
    """
    n = MAX_ENUMERATION_VARS
    problem = create_binary_problem_with_lp_gap(n)
    verifier = IndependentVerifier(problem)

    # Optymalne rozwiązanie całkowitoliczbowe: x_0=1, x_1=1, reszta=0 (wartość celu = 2.0)
    assignment = {f"x_{i}": 1.0 if i < 2 else 0.0 for i in range(n)}
    candidate = SolverCandidate(
        candidate_id="cand_opt",
        assignment=assignment,
        claimed_objective=2.0,
        claimed_status="optimal",
    )

    report = verifier.verify(candidate)

    assert report.feasible is True
    assert report.verdict == Verdict.PASS
    # Relaksacja LP ma lukę (1.5 vs 2.0), ale enumeracja dowodzi globalnej optymalności
    assert report.optimality_proven is True
    assert report.dual_bound == pytest.approx(2.0, abs=1e-5)
    assert report.optimality_gap_percent == pytest.approx(0.0, abs=1e-5)


def test_enumeration_not_run_above_threshold_leaves_optimality_unproven():
    """
    Zadanie binarne o n = MAX_ENUMERATION_VARS + 1 z luką LP otrzymuje optimality_proven: False
    wraz z niepustym komunikatem wyjaśniającym w limitations.
    """
    n = MAX_ENUMERATION_VARS + 1
    problem = create_binary_problem_with_lp_gap(n)
    verifier = IndependentVerifier(problem)

    assignment = {f"x_{i}": 1.0 if i < 2 else 0.0 for i in range(n)}
    candidate = SolverCandidate(
        candidate_id="cand_opt_large",
        assignment=assignment,
        claimed_objective=2.0,
        claimed_status="optimal",
    )

    report = verifier.verify(candidate)

    assert report.feasible is True
    assert report.verdict == Verdict.PASS
    # Ponad progiem enumeracja nie jest uruchamiana: optimality_proven pozostaje False
    assert report.optimality_proven is False
    # Relaksacja LP wyznaczyła dual_bound = 1.5 z luką 25%
    assert report.dual_bound == pytest.approx(1.5, abs=1e-5)
    assert report.optimality_gap_percent == pytest.approx(25.0, abs=0.1)

    # Wymóg promptu: niepusty komunikat wyjaśniający
    explanation_found = any(
        "przekracza próg niezależnej enumeracji" in lim or "MAX_ENUMERATION_VARS" in lim
        for lim in report.limitations
    )
    assert explanation_found, f"Brak komunikatu wyjaśniającego w limitations: {report.limitations}"
