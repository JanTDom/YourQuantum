"""
YourQuantum — QAOA Solver using Qiskit Aer
Implements the full quantum execution path:
  ProblemIR → QUBO → Ising → Parametric QAOA circuit
  → Qiskit Aer execution → Parameter optimisation → Decoded candidates
  → Independent verification in caller.

This module does NOT call LLM for results.
All parameter values come from the classical optimiser.
All bitstrings come from actual circuit measurement.
"""
from __future__ import annotations

import math
import time
import traceback
import uuid
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from backend.domain.evaluator import ExpressionEvaluator
from backend.domain.problem_ir import (
    ComputeBudget, ConstraintType, ObjectiveDirection, ProblemIR, VariableDomain,
)
from backend.solvers.base import (
    ComputeSource, ExecutionStatus, MathStatus,
    ResourceEstimate, SolverAdapter, SolverResult,
)
from backend.solvers.quantum.qubo import QUBOEncoder, QUBOEncoding, QUBOEncodingError


QISKIT_AVAILABLE = True
try:
    from qiskit import QuantumCircuit
    from qiskit.circuit import Parameter, ParameterVector
    from qiskit_aer import AerSimulator
    from qiskit_aer.primitives import Sampler as AerSampler
    from scipy.optimize import minimize as scipy_minimize
except ImportError as _e:
    QISKIT_AVAILABLE = False
    _QISKIT_IMPORT_ERROR = str(_e)


@dataclass
class QAOARunRecord:
    """Full audit record of a QAOA execution."""
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    problem_id: str = ""
    encoding_id: str = ""
    backend_name: str = "aer_simulator"
    execution_mode: str = "QUANTUM_CIRCUIT_SIMULATION"

    # Circuit metadata
    n_qubits: int = 0
    p_layers: int = 1
    circuit_depth: int | None = None
    circuit_gate_count: int | None = None
    two_qubit_gate_count: int = 0
    single_qubit_gate_count: int = 0

    # Optimisation
    shots: int = 1024
    seed: int = 42
    n_evaluations: int = 0
    final_params: list[float] = field(default_factory=list)
    final_energy: float | None = None
    converged: bool = False
    optimiser: str = "COBYLA"
    multi_start_attempts: int = 1

    # Quantum Physics & Amplification Metrics
    warm_started: bool = True
    relaxation_energy: float | None = None
    initial_thetas: list[float] = field(default_factory=list)
    ground_state_prob: float | None = None
    random_guess_prob: float | None = None
    amplification_factor: float | None = None

    # Results
    sample_distribution: dict[str, int] = field(default_factory=dict)
    top_k_bitstrings: list[str] = field(default_factory=list)
    top_k_energies: list[float] = field(default_factory=list)

    # Timing
    compile_time_seconds: float = 0.0
    optimise_time_seconds: float = 0.0
    sample_time_seconds: float = 0.0
    total_time_seconds: float = 0.0

    # Honest metadata
    memory_estimate_bytes: int = 0
    notes: list[str] = field(default_factory=list)


class QAOAAdapter(SolverAdapter):
    """
    QAOA adapter using Qiskit Aer ideal statevector simulation.
    Supported: binary optimisation problems encodeable in QUBO.
    Not supported: non-binary variables, constraints requiring auxiliary qubits
    that would exceed memory.
    """

    MAX_QUBITS_STATEVECTOR = 24   # 16 * 2^24 = 256 MB complex128
    DEFAULT_P_LAYERS = 1
    DEFAULT_SHOTS = 1024
    DEFAULT_SEED = 42

    def __init__(
        self,
        mode: str = "ideal_statevector",
        depolarizing_p1: float = 0.002,
        depolarizing_p2: float = 0.02,
    ):
        self.mode = mode
        self.depolarizing_p1 = depolarizing_p1
        self.depolarizing_p2 = depolarizing_p2

    @property
    def name(self) -> str:
        return "qaoa_aer"

    @property
    def version(self) -> str:
        if not QISKIT_AVAILABLE:
            return "not_installed"
        try:
            import qiskit_aer
            return f"qiskit-aer-{qiskit_aer.__version__}"
        except Exception:
            return "unknown"

    def check_available(self) -> tuple[bool, str | None]:
        if not QISKIT_AVAILABLE:
            return False, f"Qiskit / Aer not installed: {_QISKIT_IMPORT_ERROR}"
        return True, None

    def supports(self, problem: ProblemIR) -> bool:
        if not QISKIT_AVAILABLE:
            return False
        if not problem.is_ready_to_solve:
            return False
        for var in problem.variables:
            if var.domain != VariableDomain.BINARY:
                return False
        n = len(problem.variables)
        return 1 <= n <= self.MAX_QUBITS_STATEVECTOR

    def estimate_resources(self, problem: ProblemIR) -> ResourceEstimate:
        n = len(problem.variables)
        # statevector: 16 * 2^n bytes (complex128)
        mem_bytes = 16 * (2 ** n)
        mem_mb = mem_bytes / (1024 * 1024)
        # rough time: 0.1s per COBYLA eval * n * 100 evals
        est_time = 0.1 * n * 100 * self.DEFAULT_P_LAYERS
        return ResourceEstimate(
            estimated_time_seconds=est_time,
            estimated_memory_mb=mem_mb,
            qubit_count=n,
            notes=(
                f"QAOA p=1, statevector simulation. "
                f"Memory: ~{mem_mb:.1f} MB for {n} qubits."
            ),
        )

    def solve(self, problem: ProblemIR, budget: ComputeBudget) -> SolverResult:
        result = SolverResult(
            solver_name=self.name,
            solver_version=self.version,
            problem_id=problem.problem_id,
            source=ComputeSource.CLASSICAL_SOLVER,
        )
        if not QISKIT_AVAILABLE:
            result.execution_status = ExecutionStatus.FAILED
            result.math_status = MathStatus.UNSUPPORTED
            result.error_message = "Qiskit not installed."
            return result

        start_total = time.monotonic()
        try:
            record, result = self._run_qaoa(problem, budget, result)
            result.metadata["qaoa_run_record"] = record.__dict__
            if result.execution_status == ExecutionStatus.COMPLETED:
                evidence: dict[str, Any] = {
                    "backend_name": record.backend_name,
                    "shots": record.shots,
                    "n_qubits": record.n_qubits,
                    "depth": record.circuit_depth or 0,
                    "seed": record.seed,
                    "histogram": record.sample_distribution,
                    "execution_mode": record.execution_mode,
                }
                if record.execution_mode == "noise_simulation":
                    evidence["noise_model"] = {
                        "type": "depolarizing",
                        "p1": self.depolarizing_p1,
                        "p2": self.depolarizing_p2,
                    }
                result.execution_evidence = evidence
                result.source = ComputeSource.QUANTUM_CIRCUIT_SIMULATION
        except Exception as exc:
            result.execution_status = ExecutionStatus.FAILED
            result.math_status = MathStatus.UNKNOWN
            result.error_message = f"QAOA error: {exc}\n{traceback.format_exc()}"
        result.solve_time_seconds = time.monotonic() - start_total
        result.limitations = self._qaoa_limitations()
        return result

    # ------------------------------------------------------------------
    # Core QAOA implementation
    # ------------------------------------------------------------------

    def _run_qaoa(
        self,
        problem: ProblemIR,
        budget: ComputeBudget,
        result: SolverResult,
    ) -> tuple[QAOARunRecord, SolverResult]:
        record = QAOARunRecord(
            problem_id=problem.problem_id,
            execution_mode=self.mode,
            shots=budget.quantum_shots,
            seed=self.DEFAULT_SEED,
        )

        # Step 1: Encode to QUBO
        t0 = time.monotonic()
        encoder = QUBOEncoder()
        try:
            encoding = encoder.encode(problem)
        except QUBOEncodingError as e:
            result.execution_status = ExecutionStatus.FAILED
            result.math_status = MathStatus.UNSUPPORTED
            result.error_message = f"QUBO encoding failed: {e}"
            return record, result

        record.encoding_id = encoding.encoding_id
        record.n_qubits = encoding.n_qubits
        record.notes.extend(encoding.notes)

        if not encoding.verified and encoding.verification_error:
            record.notes.append(f"WARNING: {encoding.verification_error}")

        # Check memory budget
        mem_bytes = 16 * (2 ** encoding.n_qubits)
        record.memory_estimate_bytes = mem_bytes
        mem_mb = mem_bytes / (1024 * 1024)
        if mem_mb > budget.memory_mb:
            result.execution_status = ExecutionStatus.FAILED
            result.math_status = MathStatus.UNSUPPORTED
            result.error_message = (
                f"Insufficient memory: {encoding.n_qubits} qubits require "
                f"~{mem_mb:.1f} MB statevector but budget is {budget.memory_mb} MB."
            )
            return record, result

        record.compile_time_seconds = time.monotonic() - t0

        # Step 2: Continuous Relaxation & Warm-Start Preparation
        t1 = time.monotonic()
        n = encoding.n_qubits
        p = self.DEFAULT_P_LAYERS

        x_star, relaxed_energy = self._compute_continuous_relaxation(encoding)
        record.relaxation_energy = relaxed_energy
        initial_thetas = [float(2.0 * math.asin(math.sqrt(float(xi)))) for xi in x_star]
        record.initial_thetas = initial_thetas

        gamma_params = ParameterVector("γ", p)
        beta_params = ParameterVector("β", p)
        circuit = self._build_qaoa_circuit(
            encoding, gamma_params, beta_params, p, initial_thetas=initial_thetas
        )
        ops = circuit.count_ops()
        record.circuit_depth = circuit.depth()
        record.circuit_gate_count = circuit.size()
        record.two_qubit_gate_count = ops.get("cx", 0)
        record.single_qubit_gate_count = ops.get("rz", 0) + ops.get("rx", 0) + ops.get("ry", 0) + ops.get("h", 0)
        record.p_layers = p

        # Step 3: Optimise parameters
        t2 = time.monotonic()
        if self.mode == "noise_simulation":
            from qiskit_aer.noise import NoiseModel, depolarizing_error
            noise_model = NoiseModel()
            if self.depolarizing_p1 > 0:
                err1 = depolarizing_error(self.depolarizing_p1, 1)
                noise_model.add_all_qubit_quantum_error(err1, ["rx", "ry", "rz", "h"])
            if self.depolarizing_p2 > 0:
                err2 = depolarizing_error(self.depolarizing_p2, 2)
                noise_model.add_all_qubit_quantum_error(err2, ["cx"])
            simulator = AerSimulator(noise_model=noise_model)
        else:
            simulator = AerSimulator(method="statevector")
        n_evals = [0]
        eval_times = []
        time_limit = budget.wall_time_seconds - (time.monotonic() - t1)
        best_seen_params = np.zeros(2 * p, dtype=np.float64)
        best_seen_energy = [float("inf")]

        def objective(params: np.ndarray) -> float:
            if time.monotonic() - t1 > time_limit:
                raise TimeoutError("QAOA optimisation timed out.")
            n_evals[0] += 1
            bound = dict(zip(
                list(gamma_params) + list(beta_params),
                params.tolist()
            ))
            bound_circuit = circuit.assign_parameters(bound)
            meas_circuit = bound_circuit.copy()
            meas_circuit.measure_all()
            job = simulator.run(meas_circuit, shots=256, seed_simulator=self.DEFAULT_SEED)
            counts = job.result().get_counts()
            energy = 0.0
            total = sum(counts.values())
            for bitstring, count in counts.items():
                x = self._bitstring_to_array(bitstring, n)
                energy += (count / total) * encoding.eval_qubo_energy(x)
            if energy < best_seen_energy[0]:
                best_seen_energy[0] = energy
                best_seen_params[:] = params
            return energy

        # TQA (Trotterized Quantum Annealing) adiabatic ramp initialization
        dt = 0.75
        tqa_gamma = [(l + 0.5) / p * dt for l in range(p)]
        tqa_beta = [(1.0 - (l + 0.5) / p) * dt for l in range(p)]
        cand1 = np.array(tqa_gamma + tqa_beta, dtype=np.float64)

        # Perturbed adiabatic candidate
        cand2 = np.array([g * 1.3 for g in tqa_gamma] + [b * 0.7 for b in tqa_beta], dtype=np.float64)

        # Pi-scaled phase candidate
        cand3 = np.array(
            [np.pi / (4 * p) * (l + 1) for l in range(p)] +
            [np.pi / 2 * (1.0 - l / p) for l in range(p)],
            dtype=np.float64
        )
        candidate_starts = [cand1, cand2, cand3]
        record.multi_start_attempts = len(candidate_starts)

        # Pre-screen initial candidate trajectories
        best_x0 = cand1
        best_init_e = float("inf")
        for cand in candidate_starts:
            try:
                e_val = objective(cand)
                if e_val < best_init_e:
                    best_init_e = e_val
                    best_x0 = cand
            except Exception:
                pass

        x0 = best_x0
        best_seen_params[:] = x0
        opt_result = None
        converged = False
        try:
            opt_result = scipy_minimize(
                objective,
                x0,
                method="COBYLA",
                options={
                    "maxiter": min(500, max(50, int(time_limit / 0.1))),
                    "rhobeg": 0.6,
                },
            )
            converged = opt_result.success
            record.final_energy = float(opt_result.fun)
        except TimeoutError:
            result.warnings.append("QAOA optimisation timed out; using best parameters found.")
        except Exception as e:
            result.warnings.append(f"QAOA optimiser warning: {e}")

        record.n_evaluations = n_evals[0]
        record.converged = converged
        record.optimise_time_seconds = time.monotonic() - t2

        if opt_result is not None:
            final_params_arr = opt_result.x
        else:
            final_params_arr = best_seen_params
        record.final_params = final_params_arr.tolist()

        # Step 4: Final sampling with optimal parameters
        t3 = time.monotonic()
        bound_final = dict(zip(
            list(gamma_params) + list(beta_params),
            final_params_arr.tolist()
        ))
        final_circuit = circuit.assign_parameters(bound_final)
        final_circuit.measure_all()
        final_job = simulator.run(
            final_circuit,
            shots=budget.quantum_shots,
            seed_simulator=self.DEFAULT_SEED,
        )
        counts = final_job.result().get_counts()
        record.sample_distribution = dict(counts)
        record.sample_time_seconds = time.monotonic() - t3
        record.total_time_seconds = time.monotonic() - t1

        # Step 5: Evaluate all unique bitstring samples on original ProblemIR
        evaluator = ExpressionEvaluator(problem.expressions)
        candidates_evaluated: list[dict[str, Any]] = []

        for bitstring, count in counts.items():
            x = self._bitstring_to_array(bitstring, n)
            qubo_energy = encoding.eval_qubo_energy(x)
            assignment = encoding.decode_bitstring(bitstring)

            # Evaluate feasibility on original constraints
            is_feasible = True
            for constraint in problem.constraints:
                if not constraint.hard:
                    continue
                try:
                    lhs_v = evaluator.evaluate(constraint.lhs_expression_id, assignment)
                    rhs_v = evaluator.evaluate(constraint.rhs_expression_id, assignment) if constraint.rhs_expression_id else 0.0
                    if constraint.type == ConstraintType.EQUALITY and abs(lhs_v - rhs_v) > 1e-5:
                        is_feasible = False
                        break
                    elif constraint.type == ConstraintType.INEQUALITY_LE and (lhs_v - rhs_v) > 1e-5:
                        is_feasible = False
                        break
                    elif constraint.type == ConstraintType.INEQUALITY_GE and (rhs_v - lhs_v) > 1e-5:
                        is_feasible = False
                        break
                except Exception:
                    is_feasible = False
                    break

            # Recompute true objective from original ProblemIR expression
            true_obj: float | None = None
            if problem.objectives:
                try:
                    val = evaluator.evaluate(problem.objectives[0].expression_id, assignment)
                    if math.isfinite(val):
                        true_obj = val
                except Exception:
                    true_obj = None

            candidates_evaluated.append({
                "bitstring": bitstring,
                "count": count,
                "qubo_energy": qubo_energy,
                "assignment": assignment,
                "feasible": is_feasible,
                "true_obj": true_obj,
            })

        feasible_pool = [c for c in candidates_evaluated if c["feasible"]]

        if feasible_pool:
            is_min = problem.objectives and problem.objectives[0].direction == ObjectiveDirection.MINIMIZE
            feasible_pool.sort(
                key=lambda c: (
                    c["true_obj"] if c["true_obj"] is not None else float("inf")
                ) if is_min else (
                    -(c["true_obj"] if c["true_obj"] is not None else float("-inf"))
                )
            )
            best_candidate = feasible_pool[0]
            math_status = MathStatus.FEASIBLE
        elif candidates_evaluated:
            candidates_evaluated.sort(key=lambda c: c["qubo_energy"])
            best_candidate = candidates_evaluated[0]
            math_status = MathStatus.INFEASIBLE
            result.warnings.append("No feasible samples found in QAOA measurement distribution.")
        else:
            best_candidate = None
            math_status = MathStatus.UNKNOWN

        # Record top-k energies
        candidates_evaluated.sort(key=lambda c: c["qubo_energy"])
        record.top_k_bitstrings = [c["bitstring"] for c in candidates_evaluated[:5]]
        record.top_k_energies = [c["qubo_energy"] for c in candidates_evaluated[:5]]

        if best_candidate is not None:
            total_shots = sum(counts.values()) or budget.quantum_shots
            best_count = counts.get(best_candidate["bitstring"], 0)
            ground_state_prob = best_count / total_shots if total_shots > 0 else 0.0
            random_guess_prob = 1.0 / (2 ** n) if n <= 30 else 0.0
            amplification_factor = (ground_state_prob / random_guess_prob) if random_guess_prob > 0 else 1.0

            record.ground_state_prob = round(ground_state_prob, 4)
            record.random_guess_prob = round(random_guess_prob, 6)
            record.amplification_factor = round(amplification_factor, 2)

            result.assignment = best_candidate["assignment"]
            result.objective_value = best_candidate["true_obj"]
            result.execution_status = ExecutionStatus.COMPLETED
            result.math_status = math_status
            result.metadata["qubo_energy"] = best_candidate["qubo_energy"]
            result.metadata["evaluated_unique_samples"] = len(candidates_evaluated)
            result.metadata["feasible_samples_found"] = len(feasible_pool)
            result.metadata["warm_started"] = record.warm_started
            result.metadata["relaxation_energy"] = record.relaxation_energy
            result.metadata["ground_state_prob"] = record.ground_state_prob
            result.metadata["random_guess_prob"] = record.random_guess_prob
            result.metadata["amplification_factor"] = record.amplification_factor
            result.metadata["two_qubit_gate_count"] = record.two_qubit_gate_count
            result.metadata["single_qubit_gate_count"] = record.single_qubit_gate_count
            result.metadata["circuit_depth"] = record.circuit_depth
            result.metadata["p_layers"] = record.p_layers
            result.metadata["n_qubits"] = record.n_qubits
            result.metadata["multi_start_attempts"] = record.multi_start_attempts
            result.solver_backend_status = (
                f"converged={converged}, evals={n_evals[0]}, "
                f"top_bitstring={best_candidate['bitstring']}, "
                f"amplification={record.amplification_factor}x, "
                f"feasible_samples={len(feasible_pool)}/{len(candidates_evaluated)}"
            )
        else:
            result.execution_status = ExecutionStatus.FAILED
            result.math_status = MathStatus.UNKNOWN
            result.error_message = "No measurement samples obtained."

        return record, result

    def _build_qaoa_circuit(
        self,
        encoding: QUBOEncoding,
        gamma: Any,
        beta: Any,
        p: int,
        initial_thetas: list[float] | None = None,
    ) -> "QuantumCircuit":
        """
        Build the QAOA parametric circuit.
        Uses warm-start Ry rotations when available, or uniform superposition (Hadamard).
        Uses the Ising cost Hamiltonian for the phase operator.
        Uses RX gates for the mixing operator.
        """
        n = encoding.n_qubits
        qc = QuantumCircuit(n)

        # Initial state: Warm-Start Ry rotations or uniform superposition
        if initial_thetas and len(initial_thetas) == n:
            for i in range(n):
                qc.ry(initial_thetas[i], i)
        else:
            qc.h(range(n))

        for layer in range(p):
            # Cost operator: e^{-i*gamma*H_C}
            # H_C = sum_i h_i * Z_i + sum_{i<j} J_ij * Z_i * Z_j
            g = gamma[layer]
            # Single-qubit Z rotations from h
            for i in range(n):
                hi = float(encoding.h[i])  # type: ignore[index]
                if abs(hi) > 1e-10:
                    qc.rz(2 * g * hi, i)
            # Two-qubit ZZ interactions from J
            for i in range(n):
                for j in range(i + 1, n):
                    jij = float(encoding.J[i, j])  # type: ignore[index]
                    if abs(jij) > 1e-10:
                        qc.cx(i, j)
                        qc.rz(2 * g * jij, j)
                        qc.cx(i, j)

            # Mixing operator: e^{-i*beta*sum_i X_i}
            b = beta[layer]
            for i in range(n):
                qc.rx(2 * b, i)

        return qc

    def _compute_continuous_relaxation(
        self, encoding: QUBOEncoding
    ) -> tuple[np.ndarray, float]:
        """
        Compute continuous quadratic relaxation in [0, 1]^n to warm-start QAOA.
        Maps optimal continuous fractions to initial single-qubit rotations Ry(theta).
        """
        n = encoding.n_qubits
        Q = encoding.Q
        if Q is None or n == 0:
            return np.full(n, 0.5), 0.0

        Q_sym = 0.5 * (Q + Q.T)

        def fun(x: np.ndarray) -> float:
            return float(x @ Q_sym @ x)

        def jac(x: np.ndarray) -> np.ndarray:
            return 2.0 * (Q_sym @ x)

        x0 = np.full(n, 0.5)
        bounds = [(0.0, 1.0) for _ in range(n)]

        try:
            opt_res = scipy_minimize(
                fun,
                x0,
                jac=jac,
                method="L-BFGS-B",
                bounds=bounds,
                options={"maxiter": 100},
            )
            # Clip between [0.05, 0.95] to retain quantum superposition & tunneling
            x_star = np.clip(opt_res.x, 0.05, 0.95)
            relaxed_energy = float(opt_res.fun) + encoding.constant_energy
            return x_star, relaxed_energy
        except Exception:
            return np.full(n, 0.5), 0.0

    @staticmethod
    def _bitstring_to_array(bitstring: str, n: int) -> np.ndarray:
        """
        Convert a Qiskit bitstring (little-endian: rightmost = qubit 0)
        to a numpy array x[i] for qubit i.
        """
        # Qiskit returns bitstrings in big-endian order for display,
        # but the indexing is little-endian.
        # We reverse to get x[0]=qubit_0.
        bits = [int(b) for b in reversed(bitstring.replace(" ", ""))]
        # Pad or truncate to n
        bits = (bits + [0] * n)[:n]
        return np.array(bits, dtype=np.float64)

    def _qaoa_limitations(self) -> list[str]:
        noise_desc = (
            f"Circuit simulation with depolarizing noise model (p1={self.depolarizing_p1}, p2={self.depolarizing_p2})."
            if self.mode == "noise_simulation"
            else "Ideal statevector quantum circuit simulation without physical noise."
        )
        return [
            "QAOA is a heuristic — global optimality is not guaranteed.",
            f"Results come from quantum circuit simulation (Qiskit Aer), not a physical QPU. {noise_desc}",
            "QAOA performance depends on the number of layers (p) and the optimiser. p=1 is a shallow circuit with limited expressibility.",
            "All candidates must be independently verified against the original ProblemIR.",
        ]
