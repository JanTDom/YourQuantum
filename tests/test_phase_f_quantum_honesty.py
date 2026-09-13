"""
Tests for Phase F: Quantum Honesty, Noise Simulation, Design QUBO, QPU Stub, and Benchmarking (F1–F6).
"""
import json
from pathlib import Path
import pytest

from backend.domain.problem_classes import DesignProblem
from backend.domain.problem_ir import ComputeBudget
from backend.domain.router import ProblemRouter
from backend.solvers.base import (
    ComputeSource, ExecutionStatus, MathStatus, SolverResult,
)
from backend.solvers.cpsat import CPSATAdapter
from backend.solvers.quantum.qaoa import QAOAAdapter
from backend.solvers.quantum.qpu_adapter import QPUAdapter
from backend.solvers.quantum.qubo import QUBOEncoder


def test_f1_quantum_evidence_validator_rejects_empty():
    """F1: Setting source=QUANTUM_CIRCUIT_SIMULATION without execution_evidence must raise ValueError."""
    with pytest.raises(ValueError, match="Integrity violation"):
        SolverResult(
            solver_name="fake_quantum",
            source=ComputeSource.QUANTUM_CIRCUIT_SIMULATION,
            execution_evidence=None,
        )

    # Missing required field
    with pytest.raises(ValueError, match="missing required quantum metrics"):
        SolverResult(
            solver_name="fake_quantum",
            source=ComputeSource.QUANTUM_CIRCUIT_SIMULATION,
            execution_evidence={"backend_name": "aer", "shots": 100},  # missing n_qubits, depth, seed, histogram
        )

    # Valid evidence passes
    valid_res = SolverResult(
        solver_name="valid_quantum",
        source=ComputeSource.QUANTUM_CIRCUIT_SIMULATION,
        execution_evidence={
            "backend_name": "aer_simulator",
            "shots": 1024,
            "n_qubits": 4,
            "depth": 12,
            "seed": 42,
            "histogram": {"0000": 500, "1111": 524},
        },
    )
    assert valid_res.source == ComputeSource.QUANTUM_CIRCUIT_SIMULATION


def test_f3_design_qubo_encoding_energy_gap():
    """F3: QUBOEncoder.encode_design creates guaranteed energy gap between feasible and incompatible states."""
    fixture_path = Path("tests/fixtures/design/healthcare_pl.json")
    assert fixture_path.exists()

    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    problem = DesignProblem(**data)

    encoder = QUBOEncoder()
    encoding = encoder.encode_design(problem)

    assert encoding.n_qubits > 0
    assert encoding.Q is not None

    # Check energy gap on healthcare problem
    # Pick a feasible configuration (1 option per lever, all compatible)
    # Lever 0: skladkowy_nfz (opt 0)
    # Lever 1: monopson_jeden_nfz (opt 0)
    # Lever 2: brak_wspolplacenia (opt 0)
    # Lever 3: decentralizacja_szpitali (opt 0)
    var_order = encoding.variable_order
    assert len(var_order) == encoding.n_qubits

    feasible_bits = [0] * encoding.n_qubits
    for lever in problem.levers:
        # Choose first option
        vid = f"x_{lever.id}_{lever.options[0].id}"
        if vid in var_order:
            feasible_bits[var_order.index(vid)] = 1

    feasible_energy = encoding.eval_qubo_energy(feasible_bits)

    # Pick an incompatible configuration:
    # Look for incompatible pair in problem.interactions
    incompat = next(i for i in problem.interactions if not i.compatible)
    incompat_bits = [0] * encoding.n_qubits
    # Activate both incompatible options
    vid_a = f"x_{incompat.lever_a_id}_{incompat.option_a_id}"
    vid_b = f"x_{incompat.lever_b_id}_{incompat.option_b_id}"
    if vid_a in var_order:
        incompat_bits[var_order.index(vid_a)] = 1
    if vid_b in var_order:
        incompat_bits[var_order.index(vid_b)] = 1

    incompat_energy = encoding.eval_qubo_energy(incompat_bits)

    # Incompatible configuration must have strictly higher energy due to penalty scaling P
    assert incompat_energy > feasible_energy, (
        f"Energy gap violated: incompat={incompat_energy} <= feasible={feasible_energy}"
    )

    # Test decode_design_solution
    bitstring = "".join(str(b) for b in feasible_bits)
    decoded = encoder.decode_design_solution(encoding, bitstring, problem)
    assert len(decoded) == len(problem.levers)
    for lever in problem.levers:
        assert lever.id in decoded
        assert decoded[lever.id] in [opt.id for opt in lever.options]


def test_f4_qaoa_noise_simulation_execution():
    """F4: QAOA in noise_simulation mode populates noise model evidence and runs with depolarizing noise."""
    fixture_path = Path("tests/fixtures/design/healthcare_pl.json")
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    problem = DesignProblem(**data)
    ir = problem.compile_to_problem_ir()
    ir.approved = True

    budget = ComputeBudget(wall_time_seconds=10.0, quantum_shots=256)

    # Run QAOA in noise simulation mode
    adapter_noise = QAOAAdapter(
        mode="noise_simulation",
        depolarizing_p1=0.005,
        depolarizing_p2=0.05,
    )
    res_noise = adapter_noise.solve(ir, budget)

    assert res_noise.execution_status == ExecutionStatus.COMPLETED
    assert res_noise.source == ComputeSource.QUANTUM_CIRCUIT_SIMULATION
    assert res_noise.execution_evidence is not None
    assert res_noise.execution_evidence["execution_mode"] == "noise_simulation"
    assert "noise_model" in res_noise.execution_evidence
    assert res_noise.execution_evidence["noise_model"]["type"] == "depolarizing"
    assert res_noise.execution_evidence["noise_model"]["p1"] == 0.005
    assert res_noise.execution_evidence["noise_model"]["p2"] == 0.05

    # Check limitations text mentions noise model
    assert any("noise model" in lim for lim in res_noise.limitations)


def test_f5_f6_qpu_adapter_stub_honesty():
    """F6: QPUAdapter explicitly declares unavailable and refuses execution with clear error."""
    qpu = QPUAdapter()
    assert qpu.name == "qpu_hardware"
    assert qpu.is_available() is False

    avail, msg = qpu.check_available()
    assert avail is False
    assert "Brak aktywnego połączenia ze sprzętowym procesorem kwantowym" in msg

    fixture_path = Path("tests/fixtures/design/healthcare_pl.json")
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    problem = DesignProblem(**data)
    ir = problem.compile_to_problem_ir()

    assert qpu.supports(ir) is False

    res = qpu.solve(ir, ComputeBudget())
    assert res.execution_status == ExecutionStatus.FAILED
    assert res.math_status == MathStatus.UNSUPPORTED
    assert res.source == ComputeSource.QUANTUM_HARDWARE
    assert "Brak aktywnego połączenia" in res.error_message
    assert any("Fizyczny procesor kwantowy" in lim for lim in res.limitations)


def test_f2_benchmark_and_router_integration():
    """F2: Benchmark results exist in benchmarks/results/ and router consumes them."""
    results_dir = Path("benchmarks/results")
    assert results_dir.exists()
    bench_files = list(results_dir.glob("*.json"))
    assert len(bench_files) >= 1, "At least one benchmark result JSON must be recorded"

    # Router should load these benchmarks
    router = ProblemRouter(benchmarks_dir=str(results_dir))
    bench_info = router._load_benchmark_influence()
    assert bench_info["loaded_count"] >= 1

    # Route healthcare instance
    fixture_path = Path("tests/fixtures/design/healthcare_pl.json")
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    problem = DesignProblem(**data)
    ir = problem.compile_to_problem_ir()

    decision = router.route(ir)
    assert decision.recommended_solver == "cpsat"
    assert "records loaded" in decision.routing_record["benchmark_influence"]
