"""
YourQuantum — FastAPI Routes
All inputs validated by Pydantic before reaching domain logic.
No business logic in route handlers.
"""
from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_session
from backend.db.models import CaseRecord, JobRecord, ProblemRecord
from backend.domain.problem_ir import (
    ComputeBudget, ProblemIR, ProblemSpec,
    Variable, VariableDomain, Objective, ObjectiveDirection,
    Constraint, ConstraintType, Assumption, ExprNode,
)
from backend.worker.runner import SOLVER_REGISTRY, enqueue_job
from backend.api.universal_engine import UniversalComputeRequest
from backend.domain.capabilities import get_capabilities_registry

router = APIRouter()


# ---------------------------------------------------------------------------
# Health & Capabilities
# ---------------------------------------------------------------------------

@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "yourquantum-api", "version": "0.1.0"}


@router.get("/health/solvers")
async def health_solvers() -> dict[str, Any]:
    """Report real availability and installation status for all registered solvers."""
    results = []
    for a in SOLVER_REGISTRY:
        avail, err = a.check_available()
        results.append({
            "name": a.name,
            "version": a.version,
            "available": avail,
            "import_error": err,
        })
    return {"solvers": results}


@router.get("/capabilities")
async def get_capabilities() -> dict[str, Any]:
    """Return live registry of engine capabilities with honest status and test references."""
    records = get_capabilities_registry()
    return {
        "capabilities": [r.model_dump(mode="json") for r in records]
    }


# ---------------------------------------------------------------------------
# Problem intake — simplified formalisation for Stage 1
# ---------------------------------------------------------------------------

class ProblemCreateRequest(BaseModel):
    description: str = Field(min_length=10)
    # Simple structured input: list of binary variable names
    binary_variables: list[str] = Field(default_factory=list)
    # Objective: coefficients per variable (linear)
    objective_coefficients: dict[str, float] = Field(default_factory=dict)
    objective_direction: str = "minimize"
    # Equality constraints: list of {"lhs": {var: coeff}, "rhs": float}
    equality_constraints: list[dict[str, Any]] = Field(default_factory=list)
    budget: ComputeBudget = Field(default_factory=ComputeBudget)
    approved: bool = Field(default=False)


class ProblemResponse(BaseModel):
    problem_id: str
    description_formalised: str
    n_variables: int
    n_constraints: int
    n_objectives: int
    approved: bool
    missing_blocking: int
    ir_summary: dict[str, Any]


@router.post("/problems", response_model=ProblemResponse, status_code=status.HTTP_201_CREATED)
async def create_problem(
    req: ProblemCreateRequest,
    session: AsyncSession = Depends(get_session),
) -> ProblemResponse:
    """
    Create a structured problem. Defaults to unapproved unless explicitly requested.
    """
    from backend.domain.problem_ir import (
        ExpressionRegistry, ExprNode, MissingInfo, MissingInfoImpact
    )

    problem_id = str(uuid.uuid4())
    expressions = ExpressionRegistry()
    variables: list[Variable] = []
    objectives: list[Objective] = []
    constraints: list[Constraint] = []

    # Build variables — ID matches the user-supplied name
    for vname in req.binary_variables:
        vid = vname
        variables.append(Variable(
            id=vid,
            name=vname,
            domain=VariableDomain.BINARY,
        ))

    # Build objective expression (linear sum with coefficients)
    if req.objective_coefficients and variables:
        direction = (ObjectiveDirection.MINIMIZE
                     if req.objective_direction.lower() == "minimize"
                     else ObjectiveDirection.MAXIMIZE)
        # Build sum node
        term_ids: list[str] = []
        for vname, coeff in req.objective_coefficients.items():
            vid = vname  # matches variable id
            var_node_id = f"vref_{vname}"
            expressions.add(ExprNode(id=var_node_id, op="var", value=vid))
            if coeff == 1.0:
                term_ids.append(var_node_id)
            else:
                const_id = f"coeff_{vname}_{uuid.uuid4().hex[:4]}"
                expressions.add(ExprNode(id=const_id, op="const", value=coeff))
                mul_id = f"mul_{vname}_{uuid.uuid4().hex[:4]}"
                expressions.add(ExprNode(id=mul_id, op="mul", children=[const_id, var_node_id]))
                term_ids.append(mul_id)

        if len(term_ids) == 1:
            obj_expr_id = term_ids[0]
        elif len(term_ids) > 1:
            obj_expr_id = f"obj_sum_{uuid.uuid4().hex[:4]}"
            expressions.add(ExprNode(id=obj_expr_id, op="sum", children=term_ids))
        else:
            obj_expr_id = f"const_zero_{uuid.uuid4().hex[:4]}"
            expressions.add(ExprNode(id=obj_expr_id, op="const", value=0.0))

        objectives.append(Objective(
            id="primary_obj",
            direction=direction,
            expression_id=obj_expr_id,
        ))

    # Build equality constraints
    for i, eq in enumerate(req.equality_constraints):
        lhs_dict: dict[str, float] = eq.get("lhs", {})
        rhs_val: float = float(eq.get("rhs", 0.0))

        lhs_term_ids: list[str] = []
        for vname, coeff in lhs_dict.items():
            var_node_id = f"cvref_{i}_{vname}"
            expressions.add(ExprNode(id=var_node_id, op="var", value=vname))
            if coeff == 1.0:
                lhs_term_ids.append(var_node_id)
            else:
                const_id = f"ccoeff_{i}_{vname}"
                expressions.add(ExprNode(id=const_id, op="const", value=coeff))
                mul_id = f"cmul_{i}_{vname}"
                expressions.add(ExprNode(id=mul_id, op="mul",
                                         children=[const_id, var_node_id]))
                lhs_term_ids.append(mul_id)

        if len(lhs_term_ids) == 1:
            lhs_expr_id = lhs_term_ids[0]
        elif len(lhs_term_ids) > 1:
            lhs_expr_id = f"clhs_sum_{i}"
            expressions.add(ExprNode(id=lhs_expr_id, op="sum", children=lhs_term_ids))
        else:
            lhs_expr_id = f"const_zero_{i}"
            expressions.add(ExprNode(id=lhs_expr_id, op="const", value=0.0))

        rhs_expr_id = f"crhs_{i}"
        expressions.add(ExprNode(id=rhs_expr_id, op="const", value=rhs_val))

        constraints.append(Constraint(
            id=f"c_{i}",
            type=ConstraintType.EQUALITY,
            lhs_expression_id=lhs_expr_id,
            rhs_expression_id=rhs_expr_id,
            hard=True,
        ))

    now = datetime.now(timezone.utc)
    ir = ProblemIR(
        problem_id=problem_id,
        description_raw=req.description,
        description_formalised=_auto_formalise(req),
        variables=variables,
        expressions=expressions,
        objectives=objectives,
        constraints=constraints,
        budget=req.budget,
        approved=req.approved,
        approved_at=now if req.approved else None,
    )

    rec = ProblemRecord(
        id=problem_id,
        description_raw=req.description,
        description_formalised=ir.description_formalised,
        approved=req.approved,
        approved_at=ir.approved_at,
        ir_json=ir.model_dump(mode="json"),
    )
    session.add(rec)
    await session.commit()

    return ProblemResponse(
        problem_id=problem_id,
        description_formalised=ir.description_formalised,
        n_variables=len(variables),
        n_constraints=len(constraints),
        n_objectives=len(objectives),
        approved=req.approved,
        missing_blocking=0,
        ir_summary={
            "variables": [v.name for v in variables],
            "objective_direction": req.objective_direction,
            "n_equality_constraints": len(constraints),
        },
    )


@router.post("/problems/{problem_id}/approve", response_model=ProblemResponse)
async def approve_problem(
    problem_id: str,
    session: AsyncSession = Depends(get_session),
) -> ProblemResponse:
    """Explicit human approval endpoint for ProblemIR before solver execution."""
    rec = await session.get(ProblemRecord, problem_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Problem not found.")

    rec.approved = True
    rec.approved_at = datetime.now(timezone.utc)
    if rec.ir_json:
        updated = dict(rec.ir_json)
        updated["approved"] = True
        updated["approved_at"] = rec.approved_at.isoformat()
        rec.ir_json = updated
    await session.commit()

    ir = ProblemIR.model_validate(rec.ir_json)
    return ProblemResponse(
        problem_id=problem_id,
        description_formalised=rec.description_formalised,
        n_variables=len(ir.variables),
        n_constraints=len(ir.constraints),
        n_objectives=len(ir.objectives),
        approved=True,
        missing_blocking=0,
        ir_summary={
            "variables": [v.name for v in ir.variables],
            "objective_direction": ir.objectives[0].direction.value if ir.objectives else "minimize",
            "n_equality_constraints": len(ir.constraints),
        },
    )


def _auto_formalise(req: ProblemCreateRequest) -> str:
    lines = [
        f"Zadanie: {req.description}",
        f"Zmienne binarne ({len(req.binary_variables)}): "
        + ", ".join(req.binary_variables) if req.binary_variables else "Brak zmiennych",
        f"Cel: {req.objective_direction} "
        + " + ".join(f"{c}·{v}" for v, c in req.objective_coefficients.items())
        if req.objective_coefficients else "Brak funkcji celu",
    ]
    if req.equality_constraints:
        lines.append(f"Ograniczenia równościowe: {len(req.equality_constraints)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Problem retrieval
# ---------------------------------------------------------------------------

@router.get("/problems/{problem_id}")
async def get_problem(
    problem_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    rec = await session.get(ProblemRecord, problem_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Problem not found.")
    return rec.ir_json


# ---------------------------------------------------------------------------
# Job management
# ---------------------------------------------------------------------------

class JobCreateRequest(BaseModel):
    problem_id: str
    solver: str = "cp_sat"
    budget: ComputeBudget = Field(default_factory=ComputeBudget)
    metadata: dict[str, Any] = Field(default_factory=dict)


class JobStatusResponse(BaseModel):
    job_id: str
    problem_id: str
    solver_name: str
    execution_status: str
    math_status: str | None
    source: str | None
    publication_status: str = "PENDING_VERIFICATION"
    created_at: str
    started_at: str | None
    completed_at: str | None
    solve_time_seconds: float | None
    objective_value: float | None
    error_message: str | None


@router.post("/jobs", status_code=status.HTTP_202_ACCEPTED)
async def create_job(
    req: JobCreateRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    # Validate solver name
    from backend.worker.runner import get_adapter_by_name
    adapter = get_adapter_by_name(req.solver)
    if adapter is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown solver: {req.solver!r}. "
                   f"Available: {[a.name for a in SOLVER_REGISTRY]}",
        )

    # Validate problem exists and is approved
    rec = await session.get(ProblemRecord, req.problem_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Problem not found.")
    if not rec.approved:
        raise HTTPException(status_code=422, detail="Problem must be approved before solving.")

    job_id = await enqueue_job(req.problem_id, req.solver, req.budget, metadata=req.metadata)
    return {"job_id": job_id, "status": "QUEUED"}



@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    session: AsyncSession = Depends(get_session),
) -> JobStatusResponse:
    job = await session.get(JobRecord, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    return JobStatusResponse(
        job_id=job.id,
        problem_id=job.problem_id,
        solver_name=job.solver_name,
        execution_status=job.execution_status,
        math_status=job.math_status,
        source=job.source,
        publication_status=job.publication_status or "PENDING_VERIFICATION",
        created_at=job.created_at.isoformat(),
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        solve_time_seconds=job.solve_time_seconds,
        objective_value=job.objective_value,
        error_message=job.error_message,
    )


@router.get("/jobs/{job_id}/result")
async def get_job_result(
    job_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    job = await session.get(JobRecord, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job.execution_status not in ("COMPLETED", "TIMED_OUT", "FAILED"):
        raise HTTPException(status_code=202, detail="Job not yet completed.")
    assignment = job.result_json.get("assignment") if job.result_json else None
    return {
        "job_id": job.id,
        "problem_id": job.problem_id,
        "execution_status": job.execution_status,
        "math_status": job.math_status,
        "source": job.source,
        "publication_status": job.publication_status or "PENDING_VERIFICATION",
        "is_verified_recommendation": job.publication_status == "PUBLISHED_VERIFIED",
        "objective_value": job.objective_value,
        "solve_time_seconds": job.solve_time_seconds,
        "assignment": assignment,
        "solver_result": job.result_json,
        "verification": job.verification_json,
        "error_message": job.error_message,
        "metadata": job.metadata_json or {},
    }


# ---------------------------------------------------------------------------
# Decision Cases (Human Dilemmas & Everyday Choices)
# ---------------------------------------------------------------------------

class CaseAnalyzeRequest(BaseModel):
    text: str = Field(min_length=3)


@router.post("/cases/analyze")
async def analyze_case(req: CaseAnalyzeRequest) -> dict[str, Any]:
    """Analyze everyday dilemma or situation into structured DecisionCase."""
    from backend.domain.llm_advisor import LLMAdvisor
    advisor = LLMAdvisor()
    case = advisor.analyze_case(req.text)
    return case.model_dump(mode="json")


@router.post("/cases")
async def save_case(
    case_data: dict[str, Any],
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Persist or update DecisionCase."""
    from backend.domain.decision_case import DecisionCase
    case = DecisionCase.model_validate(case_data)
    rec = await session.get(CaseRecord, case.id)
    if rec is None:
        rec = CaseRecord(
            id=case.id,
            title=case.title,
            context=case.context,
            status=case.status,
            created_at=case.created_at,
            updated_at=case.updated_at,
            problem_ir_id=case.problem_ir_id,
            case_json=case.model_dump(mode="json"),
        )
        session.add(rec)
    else:
        rec.title = case.title
        rec.context = case.context
        rec.status = case.status
        rec.updated_at = datetime.now(timezone.utc)
        rec.problem_ir_id = case.problem_ir_id
        rec.case_json = case.model_dump(mode="json")
    await session.commit()
    return case.model_dump(mode="json")


@router.get("/cases/{case_id}")
async def get_case(
    case_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Retrieve persisted DecisionCase."""
    rec = await session.get(CaseRecord, case_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Decision case not found.")
    return rec.case_json


@router.post("/cases/formalize")
async def formalize_case(case_data: dict[str, Any]) -> dict[str, Any]:
    """Compile structured DecisionCase with options and user answers into FormalizationResult."""
    from backend.domain.decision_case import DecisionCase
    from backend.domain.formalizer import ProblemFormalizer
    case = DecisionCase.model_validate(case_data)
    formalizer = ProblemFormalizer()
    res = formalizer.formalize_case(case)
    return {
        "description_raw": res.description_raw,
        "description_formalised": res.description_formalised,
        "binary_variables": res.binary_variables,
        "objective_direction": res.objective_direction,
        "objective_coefficients": res.objective_coefficients,
        "equality_constraints": res.equality_constraints,
        "inequality_constraints": res.inequality_constraints,
        "assumptions": res.assumptions,
        "missing_information": res.missing_information,
        "identified_archetype": res.identified_archetype,
        "break_even_point": res.break_even_point,
    }



# ---------------------------------------------------------------------------
# Problem Formalization (NLP / AI)
# ---------------------------------------------------------------------------

class FormalizeRequest(BaseModel):
    text: str = Field(min_length=3)


@router.post("/problems/formalize")
async def formalize_problem(req: FormalizeRequest) -> dict[str, Any]:
    from backend.domain.formalizer import ProblemFormalizer
    formalizer = ProblemFormalizer()
    res = formalizer.formalize(req.text)
    return {
        "description_raw": res.description_raw,
        "description_formalised": res.description_formalised,
        "binary_variables": res.binary_variables,
        "objective_direction": res.objective_direction,
        "objective_coefficients": res.objective_coefficients,
        "equality_constraints": res.equality_constraints,
        "inequality_constraints": res.inequality_constraints,
        "assumptions": res.assumptions,
        "missing_information": res.missing_information,
        "identified_archetype": res.identified_archetype,
    }


# ---------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------

@router.get("/presets")
async def get_presets() -> list[dict[str, Any]]:
    from backend.domain.presets import get_all_presets
    return [p.model_dump() for p in get_all_presets()]


# ---------------------------------------------------------------------------
# Dual-Run Benchmark (CP-SAT vs QAOA)
# ---------------------------------------------------------------------------

class BenchmarkRequest(BaseModel):
    problem_id: str
    budget: ComputeBudget = Field(default_factory=ComputeBudget)


@router.post("/benchmarks", status_code=status.HTTP_202_ACCEPTED)
async def create_benchmark(
    req: BenchmarkRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    rec = await session.get(ProblemRecord, req.problem_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Problem not found.")
    if not rec.approved:
        raise HTTPException(status_code=422, detail="Problem must be approved.")

    cp_sat_job_id = await enqueue_job(req.problem_id, "cp_sat", req.budget)
    qaoa_job_id = await enqueue_job(req.problem_id, "qaoa_aer", req.budget)

    return {
        "problem_id": req.problem_id,
        "cp_sat_job_id": cp_sat_job_id,
        "qaoa_job_id": qaoa_job_id,
        "status": "QUEUED",
    }


# ---------------------------------------------------------------------------
# Dynamic Layperson Help & Engine Capabilities
# ---------------------------------------------------------------------------

@router.get("/help")
async def get_help_knowledge():
    from backend.api.help_service import generate_help_knowledge_base
    return generate_help_knowledge_base()


@router.get("/help/snapshot")
async def get_engine_snapshot():
    from backend.api.help_service import get_dynamic_engine_snapshot
    return get_dynamic_engine_snapshot()


# ---------------------------------------------------------------------------
# Universal Multi-Domain Compute API & SDK Portal (Password Protected)
# ---------------------------------------------------------------------------

class ApiAccessVerifyRequest(BaseModel):
    password: str


@router.post("/auth/verify-api-access")
async def verify_api_access(req: ApiAccessVerifyRequest) -> dict[str, Any]:
    """Verify master API access secret and issue expiring HMAC-signed bearer token."""
    from backend.api.universal_engine import (
        create_expiring_token,
        get_master_api_secret,
        verify_master_secret,
    )
    secret = get_master_api_secret()
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Autoryzacja API nie jest skonfigurowana na serwerze (brak zmiennej środowiskowej YQ_MASTER_API_SECRET).",
        )
    if not verify_master_secret(req.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowe hasło dostępu do Kwantowego API i SDK.",
        )
    token = create_expiring_token(secret, ttl_hours=24)
    return {
        "valid": True,
        "token": token,
        "message": "Dostęp do uniwersalnego API i SDK został autoryzowany.",
        "expires_in_hours": 24,
    }


@router.get("/sdk/download")
async def download_sdk(
    request: Request,
    sdk_type: str | None = None,
    lang: str | None = None,
    key: str | None = None,
):
    """Download official zero-dependency Python or TypeScript SDK."""
    from fastapi import Response
    from backend.api.universal_engine import verify_master_secret

    auth_candidate = key or request.headers.get("authorization") or request.headers.get("x-api-key") or ""
    if not verify_master_secret(auth_candidate):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Brak uprawnień. Wymagane hasło lub klucz API do pobrania SDK.",
        )

    base_dir = os.path.dirname(os.path.dirname(__file__))
    target_type = (sdk_type or lang or "python").lower()
    if target_type in ("typescript", "ts"):
        filepath = os.path.join(base_dir, "sdk", "yourquantum_client.ts")
        filename = "yourquantum_client.ts"
        media_type = "application/typescript"
    else:
        filepath = os.path.join(base_dir, "sdk", "yourquantum_sdk.py")
        filename = "yourquantum_sdk.py"
        media_type = "text/x-python"

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Plik SDK nie został znaleziony.")

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/universal/compute")
async def universal_compute(
    req: UniversalComputeRequest,
    request: Request,
) -> dict[str, Any]:
    """
    Universal multi-domain optimization endpoint for external projects and systems.
    Solves portfolio, logistics, staffing, scheduling, and custom mathematical dilemmas.
    """
    from backend.api.universal_engine import (
        UniversalEngine,
        verify_master_secret,
    )

    auth_val = request.headers.get("authorization") or request.headers.get("x-api-key") or ""
    if not verify_master_secret(auth_val):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowy lub brakujący klucz API (nagłówek Authorization: Bearer <key> lub X-API-Key).",
        )

    try:
        engine = UniversalEngine()
        result = engine.execute(req)
        return result.model_dump()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Błąd silnika YourQuantum: {str(e)}",
        )


class VerificationCheckRequest(BaseModel):
    problem_id: str
    candidate_id: str
    assignment: dict[str, Any]
    objective_value: float | None = None
    residual: float = 0.0
    verdict: str
    sha256_hash: str
    hmac_signature: str | None = None


@router.post("/verification/check")
async def verify_audit_passport_endpoint(req: VerificationCheckRequest) -> dict[str, Any]:
    """
    B3: Independently verifies SHA-256 integrity hash and server HMAC signature of a verification report.
    Guarantees mathematically that the result was stamped by YourQuantum without tampering.
    """
    from backend.verifier.verifier import (
        build_verification_canonical_string,
        compute_verification_signatures,
    )
    import hmac

    canonical = build_verification_canonical_string(
        problem_id=req.problem_id,
        candidate_id=req.candidate_id,
        assignment=req.assignment,
        objective_value=req.objective_value,
        residual=req.residual,
        verdict=req.verdict,
    )

    expected_sha256, expected_hmac = compute_verification_signatures(canonical)

    sha256_valid = hmac.compare_digest(expected_sha256.lower(), req.sha256_hash.lower())
    hmac_valid = False
    if req.hmac_signature:
        hmac_valid = hmac.compare_digest(expected_hmac.lower(), req.hmac_signature.lower())

    if sha256_valid and hmac_valid:
        overall_status = "AUTHENTIC_VERIFIED"
        details = "Pełna weryfikacja pomyślna: integralność danych SHA-256 oraz kryptograficzna pieczęć serwera HMAC są autentyczne."
    elif sha256_valid and not req.hmac_signature:
        overall_status = "INTEGRITY_VERIFIED_UNSIGNED"
        details = "Odcisk integralności SHA-256 poprawny (dane nie uległy zmianie), brak podpisu serwera HMAC."
    elif sha256_valid and not hmac_valid:
        overall_status = "SIGNATURE_MISMATCH"
        details = "Odcisk SHA-256 zgadza się, lecz podpis serwera HMAC jest nieprawidłowy."
    else:
        overall_status = "TAMPERED"
        details = "Odcisk integralności SHA-256 nie zgadza się z zawartością raportu — dane zostały zmodyfikowane."

    return {
        "sha256_valid": sha256_valid,
        "hmac_valid": hmac_valid,
        "status": overall_status,
        "details": details,
        "canonical_string": canonical,
    }


# ---------------------------------------------------------------------------
# C1-C6: Evidence Layer Endpoints
# ---------------------------------------------------------------------------

GLOBAL_EVIDENCE_STORE: dict[str, Any] = {}


class EvidenceResearchRequest(BaseModel):
    case_id: str | None = None
    target_parameters: list[dict[str, Any]] | None = None
    max_results_per_param: int = 2


@router.post("/evidence/research")
async def conduct_evidence_research(req: EvidenceResearchRequest) -> dict[str, Any]:
    """
    C1-C5: Research missing parameters across the public web using ResearchPlanner.
    Enforces quote verification and returns validated Evidence records and conflicts.
    """
    from backend.domain.evidence.models import Evidence, ResearchQuery
    from backend.domain.evidence.planner import ResearchPlanner
    from backend.infrastructure.web_research.search_adapter import WebResearchAdapter
    from backend.infrastructure.web_research.extractor import EvidenceExtractor

    adapter = WebResearchAdapter()
    extractor = EvidenceExtractor()
    planner = ResearchPlanner(evidence_port=adapter, extractor=extractor)

    queries: list[ResearchQuery] = []
    if req.target_parameters:
        for idx, tp in enumerate(req.target_parameters):
            param_id = str(tp.get("param_id") or f"param_{idx+1}")
            q_text = str(tp.get("query_text") or tp.get("name") or param_id)
            queries.append(
                ResearchQuery(
                    id=f"rq_{uuid.uuid4().hex[:8]}",
                    target_param=param_id,
                    query_text=q_text,
                    expected_unit=tp.get("expected_unit"),
                    rationale=tp.get("rationale", ""),
                )
            )

    evidence_list, conflicts = await planner.execute_research_plan(
        queries=queries,
        max_results_per_query=req.max_results_per_param,
    )

    for ev in evidence_list:
        GLOBAL_EVIDENCE_STORE[ev.id] = ev

    return {
        "status": "COMPLETED",
        "evidence_count": len(evidence_list),
        "conflict_count": len(conflicts),
        "evidence": [ev.model_dump() for ev in evidence_list],
        "conflicts": [c.model_dump() for c in conflicts],
        "port_status": adapter.get_status(),
    }


@router.get("/evidence/{evidence_id}")
async def get_evidence_record(evidence_id: str) -> dict[str, Any]:
    """
    C2: Retrieve detailed Evidence record by ID.
    """
    ev = GLOBAL_EVIDENCE_STORE.get(evidence_id)
    if not ev:
        raise HTTPException(status_code=404, detail=f"Evidence '{evidence_id}' not found")

    return ev.model_dump() if hasattr(ev, "model_dump") else dict(ev)


# ---------------------------------------------------------------------------
# D3 / G4: DESIGN Problem Synthesis & Pareto Frontier Endpoints
# ---------------------------------------------------------------------------

@router.get("/design/fixtures/{fixture_name}")
async def get_design_fixture(fixture_name: str) -> dict[str, Any]:
    """
    Retrieve built-in DESIGN problem fixtures (e.g. healthcare_pl).
    """
    safe_name = re.sub(r"[^a-zA-Z0-9_\-]", "", fixture_name)
    fixture_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "tests", "fixtures", "design", f"{safe_name}.json"
    )
    if not os.path.exists(fixture_path):
        raise HTTPException(status_code=404, detail=f"Design fixture '{safe_name}' not found")

    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)


@router.post("/design/synthesize")
async def synthesize_design_problem(design_data: dict[str, Any]) -> dict[str, Any]:
    """
    D3 / G4: Compute full multi-lever combinatorial synthesis:
    Non-dominated Pareto frontier, lever sensitivity ranking, and optimal configuration.
    """
    from backend.domain.problem_classes import DesignProblem, compute_design_synthesis
    try:
        problem = DesignProblem.model_validate(design_data)
        synthesis = compute_design_synthesis(problem)
        return {
            "status": "COMPLETED",
            "synthesis": synthesis.model_dump(mode="json"),
            "problem": problem.model_dump(mode="json"),
        }
    except Exception as e:
        logger.exception("Design synthesis failed: %s", e)
        raise HTTPException(status_code=400, detail=f"Błąd syntezy DESIGN: {str(e)}")

