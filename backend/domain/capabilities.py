"""
YourQuantum — Dynamic Capabilities Registry
Tracks feature lifecycle (PLANNED, IMPLEMENTED, TESTED, DEPLOYED) with real test references.
Honest principle: A capability is only TESTED if automated tests actively verify it.
"""
from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

from backend.worker.runner import SOLVER_REGISTRY


class CapabilityStatus(str, Enum):
    PLANNED = "PLANNED"
    IMPLEMENTED = "IMPLEMENTED"
    TESTED = "TESTED"
    DEPLOYED = "DEPLOYED"


class CapabilityRecord(BaseModel):
    id: str
    name: str
    category: str
    status: CapabilityStatus
    test_coverage_ref: str | None = None
    description: str
    is_available: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


def get_capabilities_registry() -> list[CapabilityRecord]:
    """
    Return the live capabilities registry reflecting the true operational state of the codebase.
    """
    # Check live solver availability
    solver_status = {a.name: a.check_available() for a in SOLVER_REGISTRY}

    return [
        # Core Pipeline
        CapabilityRecord(
            id="pipe-intake-nl",
            name="Problem intake (natural language)",
            category="Core Pipeline",
            status=CapabilityStatus.TESTED,
            test_coverage_ref="tests/test_formalizer.py",
            description="LLM-assisted problem intake with cognitive fallback and missing information detection.",
        ),
        CapabilityRecord(
            id="pipe-ir-schema",
            name="Problem IR schema v0.2",
            category="Core Pipeline",
            status=CapabilityStatus.TESTED,
            test_coverage_ref="tests/test_problem_ir.py",
            description="Versioned intermediate representation with strict Pydantic validation.",
        ),
        CapabilityRecord(
            id="pipe-approval-gate",
            name="IR user approval gate",
            category="Core Pipeline",
            status=CapabilityStatus.TESTED,
            test_coverage_ref="tests/test_api_and_gate.py",
            description="Deliberate human approval required before solver execution.",
        ),
        CapabilityRecord(
            id="pipe-budget-enforcement",
            name="Compute budget enforcement",
            category="Core Pipeline",
            status=CapabilityStatus.TESTED,
            test_coverage_ref="tests/test_universal_api.py",
            description="Enforces wall time and resource limits per solver job.",
        ),
        CapabilityRecord(
            id="pipe-decomposition",
            name="Benders problem decomposition",
            category="Core Pipeline",
            status=CapabilityStatus.TESTED,
            test_coverage_ref="tests/test_hybrid_benders.py",
            description="Hybrid Benders decomposition splitting master and constraint subproblems.",
        ),

        # Classical Solvers
        CapabilityRecord(
            id="solver-cpsat",
            name="OR-Tools CP-SAT Adapter",
            category="Classical Solvers",
            status=CapabilityStatus.TESTED,
            test_coverage_ref="tests/test_audit_regressions.py",
            description="Constraint satisfaction and discrete optimisation via Google OR-Tools.",
            is_available=solver_status.get("cp_sat", (False, ""))[0],
        ),
        CapabilityRecord(
            id="solver-highs",
            name="HiGHS LP Dual Relaxation",
            category="Classical Solvers",
            status=CapabilityStatus.TESTED,
            test_coverage_ref="tests/test_dual_certificate.py",
            description="Linear programming dual bound certificate generation via SciPy HiGHS.",
        ),
        CapabilityRecord(
            id="solver-continuous",
            name="SciPy Continuous Optimization Adapter",
            category="Classical Solvers",
            status=CapabilityStatus.TESTED,
            test_coverage_ref="tests/test_phase_d_problem_classes.py",
            description="Continuous parameter optimization using SciPy HiGHS / minimize with numerical residuals.",
            is_available=solver_status.get("scipy_continuous", (False, ""))[0],
        ),
        CapabilityRecord(
            id="solver-z3",
            name="Z3 SMT Solver Adapter",
            category="Classical Solvers",
            status=CapabilityStatus.PLANNED,
            description="SMT logic solver for non-linear symbolic problems.",
            is_available=False,
        ),

        # Quantum Core
        CapabilityRecord(
            id="qcore-qubo-encoder",
            name="QUBO Matrix Encoder",
            category="Quantum Core",
            status=CapabilityStatus.TESTED,
            test_coverage_ref="tests/test_qubo.py",
            description="Problem IR to quadratic unconstrained binary optimisation matrix with penalty calibration.",
        ),
        CapabilityRecord(
            id="qcore-ising-encoder",
            name="Ising Hamiltonian Encoder",
            category="Quantum Core",
            status=CapabilityStatus.TESTED,
            test_coverage_ref="tests/test_qubo.py",
            description="Mapping binary decision variables to Pauli-Z spin operators.",
        ),
        CapabilityRecord(
            id="qcore-qaoa-aer",
            name="QAOA Circuit Simulator (Aer)",
            category="Quantum Core",
            status=CapabilityStatus.TESTED,
            test_coverage_ref="tests/test_qaoa.py",
            description="Variational Quantum Eigensolver / QAOA execution on Qiskit Aer simulator.",
            is_available=solver_status.get("qaoa_aer", (False, ""))[0],
        ),
        CapabilityRecord(
            id="qcore-warm-start",
            name="Warm-Started QAOA",
            category="Quantum Core",
            status=CapabilityStatus.TESTED,
            test_coverage_ref="tests/test_warm_start_qaoa.py",
            description="Initial state rotation biased by classical LP relaxation.",
        ),
        CapabilityRecord(
            id="qcore-noise-sim",
            name="Noise Model Simulator (Kraus / Depolarizing Channels)",
            category="Quantum Core",
            status=CapabilityStatus.TESTED,
            test_coverage_ref="tests/test_phase_f_quantum_honesty.py",
            description="Depolarizing noise model simulation (p1, p2) via Qiskit Aer for NISQ circuit benchmarking.",
            is_available=solver_status.get("qaoa_aer", (False, ""))[0],
        ),
        CapabilityRecord(
            id="qcore-qpu-hardware",
            name="Physical QPU Connectivity (Stub/Disconnected)",
            category="Quantum Core",
            status=CapabilityStatus.IMPLEMENTED,
            test_coverage_ref="tests/test_phase_f_quantum_honesty.py",
            description="Hardware adapter stub explicitly verifying lack of physical QPU connectivity.",
            is_available=solver_status.get("qpu_hardware", (False, ""))[0],
        ),

        # Verification & Robustness
        CapabilityRecord(
            id="verif-independent-check",
            name="Independent Constraint Verification",
            category="Verification",
            status=CapabilityStatus.TESTED,
            test_coverage_ref="tests/test_verifier.py",
            description="Ground-truth mathematical evaluation of candidate assignments without trusting solver.",
        ),
        CapabilityRecord(
            id="verif-dual-bound",
            name="Dual Gap & Optimality Certificate",
            category="Verification",
            status=CapabilityStatus.TESTED,
            test_coverage_ref="tests/test_dual_certificate.py",
            description="Independent lower-bound computation via LP relaxation and exhaustive enumeration.",
        ),
        CapabilityRecord(
            id="verif-sensitivity",
            name="Sensitivity & Stress Testing Engine",
            category="Verification",
            status=CapabilityStatus.TESTED,
            test_coverage_ref="tests/test_sensitivity.py",
            description="Candidate elasticity and boundary violation analysis under parameter shock.",
        ),

        # Cognitive Subsystem
        CapabilityRecord(
            id="cog-active-inference",
            name="Active Inference Loop",
            category="Cognitive Brain",
            status=CapabilityStatus.TESTED,
            test_coverage_ref="tests/test_audit_regressions.py",
            description="Self-correcting perception-hypothesis loop minimizing prediction errors.",
        ),
        CapabilityRecord(
            id="cog-episodic-memory",
            name="Episodic Memory with Tenant Scoping",
            category="Cognitive Brain",
            status=CapabilityStatus.TESTED,
            test_coverage_ref="tests/test_audit_regressions.py",
            description="Recall and consolidation of successful problem formulations without data leakage.",
        ),

        # Integrations
        CapabilityRecord(
            id="int-mcp-server",
            name="Model Context Protocol (MCP) Server",
            category="Integrations",
            status=CapabilityStatus.TESTED,
            test_coverage_ref="tests/test_mcp_server.py",
            description="Universal LLM tool integration supporting Claude, Cursor, and IDE extensions.",
        ),

        # Evidence Layer (Phase C)
        CapabilityRecord(
            id="ev-web-research",
            name="Evidence Research Layer",
            category="Evidence",
            status=CapabilityStatus.TESTED,
            test_coverage_ref="tests/test_phase_c_evidence.py",
            description="Empirical web evidence gathering with SHA-256 content hashes and verbatim quote verification.",
        ),
        CapabilityRecord(
            id="ev-conflict-detection",
            name="Multi-Source Conflict & Spread Detection",
            category="Evidence",
            status=CapabilityStatus.TESTED,
            test_coverage_ref="tests/test_phase_c_evidence.py",
            description="Automatic divergence and spread detection across conflicting web sources.",
        ),
    ]
