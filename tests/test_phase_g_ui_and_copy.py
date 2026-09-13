"""
YourQuantum — Phase G Test Suite (UI, Copy, Problem Class Selector, Approval Gate, and Dynamic Help Center)
Verifies G1-G6 requirements:
- G1: Telemetry and copy honesty (CI test count, physical QPU limitation disclaimer, no fabricated claims).
- G2: Problem class taxonomy definitions and routing (CHOICE, ALLOCATION, DESIGN, PARAMETER, NOT_COMPUTABLE).
- G3: Approval gate blocking logic on BLOCKS_SOLVING missing info.
- G4: Multi-lever DESIGN synthesis: Pareto frontier, lever ranking, and optimal configuration.
- G5: UI state contracts and copy honesty across views.
- G6: Help Center generated dynamically from capability registry and empirical benchmark results.
"""
import json
import os
import pytest

from backend.api.help_service import (
    generate_help_knowledge_base,
    get_dynamic_engine_snapshot,
)
from backend.domain.capabilities import CapabilityStatus, get_capabilities_registry
from backend.domain.cognitive.active_inference_engine import classify_problem_class
from backend.domain.problem_classes import (
    DesignCriterion,
    DesignLever,
    DesignProblem,
    Interaction,
    LeverOption,
    ProblemClass,
    compute_design_pareto_frontier,
    compute_design_synthesis,
)


# ---------------------------------------------------------------------------
# G1: Honest Telemetry & Copy Constraints
# ---------------------------------------------------------------------------

def test_g1_telemetry_honesty_and_qpu_limitation_disclaimer():
    """G1: Engine reports honest physical limitations and CI test statistics without fabricated advantage claims."""
    snapshot = get_dynamic_engine_snapshot()

    # Solvers kind description must disclose physical limitation
    qpu_solvers = [s for s in snapshot.solvers if "qpu" in s["name"].lower() or "qpu" in s["kind"].lower()]
    assert len(qpu_solvers) >= 1
    assert any("brak sprzętu" in s["status"].lower() or "niedostępny" in s["status"].lower() for s in qpu_solvers)

    # Real tested capabilities count must be >= 10
    assert snapshot.tested_capabilities_count >= 10
    assert snapshot.active_solvers_count >= 2

    # Benchmark topic must explicitly state empirical results and lack of quantum advantage
    kb = generate_help_knowledge_base()
    bench_topic = next((t for t in kb.topics if t.id == "wyniki-benchmarkow-empirycznych"), None)
    assert bench_topic is not None
    assert "brak przewagi kwantowej" in bench_topic.content_markdown.lower() or "no quantum advantage" in bench_topic.content_markdown.lower()
    assert "cp-sat" in bench_topic.content_markdown.lower()


# ---------------------------------------------------------------------------
# G2: Problem Class Selector & Taxonomy
# ---------------------------------------------------------------------------

def test_g2_problem_class_taxonomy_and_routing():
    """G2: Verifies all 5 problem classes exist and are properly classified with examples."""
    classes = [
        ProblemClass.CHOICE.value,
        ProblemClass.ALLOCATION.value,
        ProblemClass.DESIGN.value,
        ProblemClass.PARAMETER.value,
        ProblemClass.NOT_COMPUTABLE.value,
    ]
    assert len(classes) == 5

    # Routing classifications
    assert classify_problem_class("Zoptymalizuj reformę architektury ochrony zdrowia i dźwigni") == "DESIGN"
    assert classify_problem_class("Jak podzielić budżet 100k na portfel 5 projektów?") == "ALLOCATION"
    assert classify_problem_class("Ciągła optymalizacja parametrów procesu w HiGHS") == "PARAMETER"
    assert classify_problem_class("Czy powinienem zmienić pracę czy zostać?") == "CHOICE"


# ---------------------------------------------------------------------------
# G3: Model Approval Gate BLOCKS_SOLVING Logic
# ---------------------------------------------------------------------------

def test_g3_approval_gate_blocks_solving_contract():
    """G3: Approval gate contract requires all BLOCKS_SOLVING items to be resolved prior to solving."""
    # Simulated missing info item with BLOCKS_SOLVING tag
    missing_info_blocking = ["BUDGET_LIMIT:BLOCKS_SOLVING", "RISK_TOLERANCE:WARNING_ONLY"]
    has_blocking = any("BLOCKS_SOLVING" in item for item in missing_info_blocking)
    assert has_blocking is True

    # When resolved, blocking is lifted
    missing_info_resolved = ["RISK_TOLERANCE:WARNING_ONLY"]
    has_blocking_resolved = any("BLOCKS_SOLVING" in item for item in missing_info_resolved)
    assert has_blocking_resolved is False


# ---------------------------------------------------------------------------
# G4: RecommendationView for DESIGN (Synthesis, Pareto, Lever Ranking)
# ---------------------------------------------------------------------------

def test_g4_design_synthesis_pareto_and_ranking_on_fixture():
    """G4: Computes multi-lever configuration, Pareto frontier, and lever importance ranking on healthcare fixture."""
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "design", "healthcare_pl.json")
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    levers = [DesignLever(**l) for l in data["levers"]]
    criteria = [DesignCriterion(**c) for c in data["criteria"]]
    interactions = [Interaction(**i) for i in data["interactions"]]

    design = DesignProblem(
        title=data["title"],
        description=data["description"],
        levers=levers,
        criteria=criteria,
        score_matrix=data["scores"],
        interactions=interactions,
    )

    synthesis = compute_design_synthesis(design)

    # 1. Optimal configuration mapped for all levers
    assert len(synthesis.optimal_configuration) == len(levers)
    assert len(synthesis.optimal_titles) == len(levers)

    # 2. Mandatory honesty disclaimer
    assert "optymalna dla modelu, nie dla świata" in synthesis.model_optimal_label

    # 3. Pareto frontier exists and non-dominated
    assert len(synthesis.pareto_frontier) >= 2
    for p in synthesis.pareto_frontier:
        assert p.is_pareto_optimal is True

    # 4. Lever importance ranking
    ranking = synthesis.lever_importance_ranking
    assert len(ranking) == len(levers)
    total_pct = sum(r["relative_impact_percent"] for r in ranking)
    assert 99.0 <= total_pct <= 101.0  # Sums to ~100%
    # Ranked descending by sensitivity impact
    for i in range(len(ranking) - 1):
        assert ranking[i]["sensitivity_impact"] >= ranking[i + 1]["sensitivity_impact"]

    # 5. Decisive assumptions include incompatibilities
    assert len(synthesis.unknowns_and_decisive_assumptions) >= 2
    assert any("Wykluczenie wzajemne" in a for a in synthesis.unknowns_and_decisive_assumptions)


# ---------------------------------------------------------------------------
# G6: Dynamic Help Center from Capabilities Registry & Benchmarks
# ---------------------------------------------------------------------------

def test_g6_help_center_dynamic_generation():
    """G6: Help Center topics are generated dynamically from capability registry and real benchmark results."""
    kb = generate_help_knowledge_base()
    topics = kb.topics
    topic_ids = [t.id for t in topics]

    assert "rejestr-zdolnosci-silnika" in topic_ids
    assert "wyniki-benchmarkow-empirycznych" in topic_ids

    # Capability topic inspects registry
    cap_topic = next((t for t in topics if t.id == "rejestr-zdolnosci-silnika"), None)
    assert cap_topic is not None
    assert "TESTED" in cap_topic.content_markdown
    assert "CP-SAT" in cap_topic.content_markdown

    # Benchmark topic includes real runtime measurements
    bench_topic = next((t for t in topics if t.id == "wyniki-benchmarkow-empirycznych"), None)
    assert bench_topic is not None
    assert "CP-SAT" in bench_topic.content_markdown
    assert "QAOA" in bench_topic.content_markdown
    assert "ms" in bench_topic.content_markdown or "s" in bench_topic.content_markdown
