"""
YourQuantum — QPU Hardware Stub Adapter
Honest interface representing physical Quantum Processing Units (QPU).
Explicitly marks physical QPU execution as unavailable in current production deployment,
preventing any false claims of physical quantum execution when running classical simulations.
"""
from __future__ import annotations

from backend.domain.problem_ir import ComputeBudget, ProblemIR
from backend.solvers.base import (
    ComputeSource, ExecutionStatus, MathStatus,
    ResourceEstimate, SolverAdapter, SolverResult,
)


class QPUAdapter(SolverAdapter):
    """
    Adapter stub for physical Quantum Processing Units (e.g. IBM Quantum, Rigetti, IonQ, QuEra).
    Currently unavailable in production — all quantum execution is performed via circuit simulation.
    """

    @property
    def name(self) -> str:
        return "qpu_hardware"

    @property
    def version(self) -> str:
        return "disconnected-stub-v1"

    def is_available(self) -> bool:
        """Explicitly returns False to indicate physical QPU is not connected."""
        return False

    def check_available(self) -> tuple[bool, str | None]:
        return (
            False,
            "Brak aktywnego połączenia ze sprzętowym procesorem kwantowym (QPU). "
            "Dostępne są wyłącznie symulatory obwodów kwantowych (Aer).",
        )

    def supports(self, problem: ProblemIR) -> bool:
        """Physical QPU is not enabled for any problem class in current environment."""
        return False

    def estimate_resources(self, problem: ProblemIR) -> ResourceEstimate:
        return ResourceEstimate(
            estimated_time_seconds=0.0,
            estimated_memory_mb=0.0,
            notes="QPU hardware is disconnected.",
        )

    def solve(self, problem: ProblemIR, budget: ComputeBudget) -> SolverResult:
        """
        Refuses execution and returns an honest, explicit failure explaining lack of physical QPU.
        """
        result = SolverResult(
            solver_name=self.name,
            solver_version=self.version,
            problem_id=problem.problem_id,
            execution_status=ExecutionStatus.FAILED,
            math_status=MathStatus.UNSUPPORTED,
            source=ComputeSource.QUANTUM_HARDWARE,
        )
        result.error_message = (
            "Brak aktywnego połączenia ze sprzętowym procesorem kwantowym (QPU). "
            "Dostępne są wyłącznie symulatory obwodów kwantowych (Aer)."
        )
        result.limitations = [
            "Fizyczny procesor kwantowy (QPU) nie jest podłączony w obecnym środowisku.",
            "Wszelkie algorytmy kwantowe w YourQuantum uruchamiane są w trybie symulacji (Qiskit Aer).",
            "Symulacja obwodów kwantowych na procesorach klasycznych nie stanowi obliczeń kwantowych na QPU.",
        ]
        return result
