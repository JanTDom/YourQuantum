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

    def __post_init__(self) -> None:
        if self.source == ComputeSource.QUANTUM_CIRCUIT_SIMULATION:
            has_record = bool(self.metadata.get("qaoa_run_record")) or bool(self.execution_evidence)
            if not has_record:
                raise ValueError(
                    "Integrity violation: source cannot be QUANTUM_CIRCUIT_SIMULATION "
                    "without circuit execution evidence (metadata['qaoa_run_record'] or execution_evidence)."
                )


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
