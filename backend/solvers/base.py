"""
YourQuantum — Solver Adapter Interface
All classical and quantum adapters implement SolverAdapter.
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from backend.domain.problem_ir import ComputeBudget, ProblemIR


class ExecutionStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    TIMED_OUT = "TIMED_OUT"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class MathStatus(str, Enum):
    FEASIBLE = "FEASIBLE"
    OPTIMAL = "OPTIMAL"
    INFEASIBLE = "INFEASIBLE"
    UNBOUNDED = "UNBOUNDED"
    UNKNOWN = "UNKNOWN"
    MODEL_INVALID = "MODEL_INVALID"
    UNSUPPORTED = "UNSUPPORTED"


class ComputeSource(str, Enum):
    CLASSICAL_SOLVER = "CLASSICAL_SOLVER"
    QUANTUM_CIRCUIT_SIMULATION = "QUANTUM_CIRCUIT_SIMULATION"
    QUANTUM_HARDWARE = "QUANTUM_HARDWARE"


@dataclass
class ResourceEstimate:
    estimated_time_seconds: float
    estimated_memory_mb: float
    qubit_count: int | None = None        # for quantum
    circuit_depth: int | None = None      # for quantum
    notes: str | None = None


@dataclass
class SolverResult:
    candidate_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    solver_name: str = ""
    solver_version: str = ""
    problem_id: str = ""

    execution_status: ExecutionStatus = ExecutionStatus.FAILED
    math_status: MathStatus = MathStatus.UNKNOWN
    source: ComputeSource = ComputeSource.CLASSICAL_SOLVER

    objective_value: float | None = None
    assignment: dict[str, Any] = field(default_factory=dict)

    solve_time_seconds: float = 0.0
    memory_used_mb: float | None = None

    # Optimality evidence
    lower_bound: float | None = None
    optimality_gap: float | None = None
    certificate: dict[str, Any] | None = None
    numerical_residual: float | None = None

    # Metadata
    solver_backend_status: str = ""    # raw status string from backend
    warnings: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    error_message: str | None = None
    completed_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    execution_evidence: dict[str, Any] | None = None

    def _validate_quantum_evidence(self) -> None:
        if getattr(self, "source", None) == ComputeSource.QUANTUM_CIRCUIT_SIMULATION:
            evidence = getattr(self, "execution_evidence", None)
            meta = getattr(self, "metadata", {}) or {}
            if not evidence and meta.get("qaoa_run_record"):
                rec = meta["qaoa_run_record"]
                if isinstance(rec, dict):
                    evidence = {
                        "backend_name": rec.get("backend_name"),
                        "shots": rec.get("shots"),
                        "n_qubits": rec.get("n_qubits"),
                        "depth": rec.get("circuit_depth"),
                        "seed": rec.get("seed"),
                        "histogram": rec.get("sample_distribution"),
                    }
                    object.__setattr__(self, "execution_evidence", evidence)

            if not evidence:
                raise ValueError(
                    "Integrity violation: source cannot be QUANTUM_CIRCUIT_SIMULATION "
                    "without execution_evidence containing real circuit simulation parameters."
                )

            required_keys = {"backend_name", "shots", "n_qubits", "depth", "seed"}
            missing = required_keys - set(evidence.keys())
            if missing:
                raise ValueError(
                    f"Integrity violation: execution_evidence missing required quantum metrics: {sorted(missing)}"
                )

            if not ("histogram" in evidence or "sample_distribution" in evidence):
                raise ValueError(
                    "Integrity violation: execution_evidence must contain 'histogram' or 'sample_distribution'."
                )

    _initialized: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        self._validate_quantum_evidence()
        object.__setattr__(self, "_initialized", True)

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        if getattr(self, "_initialized", False) and name in ("source", "execution_evidence") and getattr(self, "source", None) == ComputeSource.QUANTUM_CIRCUIT_SIMULATION:
            self._validate_quantum_evidence()


class SolverAdapter(ABC):
    """
    Abstract base for all solver adapters.
    Contracts:
    - supports() is pure and fast (no I/O).
    - estimate_resources() is fast and approximate.
    - solve() respects budget.wall_time_seconds and budget.memory_mb.
    - solve() never raises to the caller — returns SolverResult with FAILED.
    """

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def version(self) -> str: ...

    @abstractmethod
    def supports(self, problem: ProblemIR) -> bool:
        """Return True iff this adapter can attempt the problem."""
        ...

    @abstractmethod
    def estimate_resources(
        self, problem: ProblemIR
    ) -> ResourceEstimate:
        """Return a fast approximate resource estimate."""
        ...

    @abstractmethod
    def solve(
        self, problem: ProblemIR, budget: ComputeBudget
    ) -> SolverResult:
        """
        Attempt to solve. Must:
        - Respect budget.wall_time_seconds and budget.memory_mb.
        - Return a SolverResult even on failure.
        - Never raise an unhandled exception.
        - Populate limitations honestly.
        """
        ...

    def check_available(self) -> tuple[bool, str | None]:
        """
        Verify that underlying solver libraries and dependencies are installed and accessible.
        Returns: (True, None) if available, or (False, "error message") if missing dependencies.
        """
        return True, None

    def _base_limitations(self, math_status: MathStatus) -> list[str]:
        lims: list[str] = []
        if math_status not in (MathStatus.OPTIMAL,):
            lims.append("Global optimality not proven by this run.")
        lims.append(
            "Model-optimal result does not guarantee real-world validity."
        )
        return lims
