"""
YourQuantum — Active Inference Engine & Cognitive Orchestrator
Coordinates the cybernetic perception-hypothesis-action-verification loop based on
Karl Friston's Free Energy Principle and neurobiological global workspace theory.
"""
from __future__ import annotations

import hashlib
import logging
import re
import unicodedata
from typing import Any, Literal
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.cognitive.cognitive_port import CognitiveReasoningPort, FormalizationResult
from backend.domain.cognitive.constraint_sanity import check_constraints_sanity
from backend.domain.cognitive.episodic_memory import EpisodicMemoryRepository
from backend.domain.cognitive.quality_gate import assess_input_quality
from backend.domain.cognitive.workspace import EnergyBudget, GlobalWorkspace
from backend.domain.decision_case import Criterion, DecisionCase, InputQuality, Option
from backend.domain.problem_classes import NotComputableReport, ProblemClass, evaluate_problem_computability
from backend.domain.problem_ir import (
    ConstraintType,
    ExprNode,
    ObjectiveDirection,
    ProblemIR,
    VariableDomain,
)
from backend.verifier.verifier import Verdict, VerificationReport

logger = logging.getLogger(__name__)

POLISH_STOPWORDS = {
    "i", "w", "z", "ze", "o", "a", "oraz", "na", "do", "od", "po", "dla",
    "czy", "się", "sie", "jest", "to", "nie", "jak", "co", "albo", "lub",
    "że", "ze", "by", "aby", "jaki", "jaka", "jakie", "mam", "między",
    "miedzy", "który", "ktora", "ktore", "które", "ten", "ta", "tych", "tym",
    "bardzo", "tylko", "może", "moze", "gdy", "przy"
}

POLISH_SUFFIXES = tuple(sorted([
    "owych", "owego", "acjami", "eniem", "ności",
    "acja", "acje", "acji", "acją",
    "ami", "ach", "ych", "ego", "emu", "iej", "owi", "em", "ie", "om",
    "am", "ą", "ę", "y", "e", "a", "u", "i", "ć", "ów", "ow"
], key=len, reverse=True))


def _stem_polish(word: str) -> str:
    for sfx in POLISH_SUFFIXES:
        if word.endswith(sfx) and len(word) - len(sfx) >= 3:
            return word[: -len(sfx)]
    return word


def compute_problem_fingerprint(query: str) -> str:
    """
    Generate a structural fingerprint hash for associative episodic recall.
    Uses NFKC normalization, Polish stopwords filtering, and stemming.
    """
    normalized = unicodedata.normalize("NFKC", query.lower())
    words = re.findall(r"\b[^\W\d_]{3,}\b", normalized, flags=re.UNICODE)
    meaningful = [w for w in words if w not in POLISH_STOPWORDS]
    stems = [_stem_polish(w) for w in meaningful]
    sorted_unique = sorted(set(stems))
    token_repr = "_".join(sorted_unique[:10]) if sorted_unique else "empty_query"
    fp_hash = hashlib.sha256(token_repr.encode("utf-8")).hexdigest()[:16]
    return f"fp_{fp_hash}_{len(sorted_unique)}"


class ProblemClassification(BaseModel):
    problem_class: str = ProblemClass.CHOICE.value
    confidence: float = 0.5
    reason: str = ""
    computable: bool = True
    reframe_suggestions: list[str] = Field(default_factory=list)


def heuristic_classify_problem(query: str, options_count: int = 0) -> ProblemClassification:
    """
    Offline regex heuristic fallback with confidence <= 0.5 (N4).
    Distinguishes CHOICE dilemmas from multi-lever DESIGN problems even if 'system' is mentioned.
    """
    lower = query.lower()

    # 1. Check uncomputable triggers
    is_computable, nc_report = evaluate_problem_computability(query)
    if not is_computable and nc_report:
        return ProblemClassification(
            problem_class=ProblemClass.NOT_COMPUTABLE.value,
            confidence=0.5,
            reason=nc_report.reason,
            computable=False,
            reframe_suggestions=nc_report.reframe_suggestions,
        )

    # 2. Check CHOICE dilemma patterns first (e.g. "system alarmowy czy kamery", "wybór między X a Y")
    is_dilemma = (
        ("czy" in lower and any(w in lower for w in ["czy", "albo", "zostać", "zostac", "wybrać", "wybrac", "kupić", "kupic", "wynająć", "wynajac"]))
        or ("wybór między" in lower or "wybor miedzy" in lower)
        or ("albo" in lower and "albo" in lower[lower.find("albo")+4:])
        or (" czy " in lower)
        or (options_count >= 2)
    )
    if is_dilemma:
        return ProblemClassification(
            problem_class=ProblemClass.CHOICE.value,
            confidence=0.5,
            reason="Wykryto dylemat wyboru pomiędzy wariantami decyzyjnymi.",
            computable=True,
            reframe_suggestions=[],
        )

    # 3. Continuous parameter optimization
    if re.search(r"\b(ciągł|parametr|hi-ghs|highs|scipy|równan|nieliniow)\b", lower):
        return ProblemClassification(
            problem_class=ProblemClass.PARAMETER.value,
            confidence=0.5,
            reason="Wykryto optymalizację zmiennych ciągłych lub estymację parametrów.",
            computable=True,
            reframe_suggestions=[],
        )

    # 4. Allocation (knapsack, portfolio, scheduling)
    if re.search(r"\b(portfel|alokac|budżet|budzet|plecak|koszyk|projekty|inwestycj|udźwig)\b", lower):
        return ProblemClassification(
            problem_class=ProblemClass.ALLOCATION.value,
            confidence=0.5,
            reason="Wykryto zagadnienie alokacji zasobów lub problem plecakowy pod ograniczeniami.",
            computable=True,
            reframe_suggestions=[],
        )

    # 5. Multi-lever systemic Design (requires genuine systemic reform/levers, not just the word 'system')
    if re.search(r"\b(dźwigni|wielopoziom|reforma|architektur.*system|syntez.*system|design|ochron.*zdrow|system.*ochron|system.*emeryt|system.*podatk)", lower):
        return ProblemClassification(
            problem_class=ProblemClass.DESIGN.value,
            confidence=0.5,
            reason="Wykryto zagadnienie syntezy wielodźwigniowej architektury lub reformy systemowej.",
            computable=True,
            reframe_suggestions=[],
        )

    return ProblemClassification(
        problem_class=ProblemClass.CHOICE.value,
        confidence=0.4,
        reason="Domyślna klasyfikacja dyskretnego wyboru wariantów.",
        computable=True,
        reframe_suggestions=[],
    )


async def classify_problem_class_async(query: str, options_count: int = 0) -> ProblemClassification:
    """
    Classify problem using LLMGateway with strict schema and fallback to offline heuristic (N4).
    """
    # Check deterministic computability first (e.g. "jaki jest sens życia", "czy bóg istnieje")
    is_comp, nc_rep = evaluate_problem_computability(query)
    if not is_comp and nc_rep:
        return ProblemClassification(
            problem_class=ProblemClass.NOT_COMPUTABLE.value,
            confidence=1.0,
            reason=nc_rep.reason,
            computable=False,
            reframe_suggestions=nc_rep.reframe_suggestions,
        )

    # For extremely short / vague inputs (< 4 words), do not classify as NOT_COMPUTABLE; let InputQualityGate handle it
    words = [w for w in query.strip().split() if len(w) > 1]
    if len(words) < 4:
        return ProblemClassification(
            problem_class=ProblemClass.CHOICE.value,
            confidence=0.5,
            reason="Zbyt krótki tekst do rzetelnej klasyfikacji LLM.",
            computable=True,
            reframe_suggestions=[],
        )

    from backend.infrastructure.llm_gateway import LLMGateway
    gateway = LLMGateway()

    if gateway.is_configured:
        schema = {
            "type": "object",
            "properties": {
                "problem_class": {
                    "type": "string",
                    "enum": ["CHOICE", "ALLOCATION", "DESIGN", "PARAMETER", "NOT_COMPUTABLE"]
                },
                "confidence": {"type": "number"},
                "reason": {"type": "string"},
                "computable": {"type": "boolean"},
                "reframe_suggestions": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["problem_class", "confidence", "reason", "computable"]
        }
        prompt = (
            "Dokonaj rygorystycznej klasyfikacji problemu decyzyjnego użytkownika do jednej z 5 klas:\n"
            "- CHOICE: wybór jednej lub kilku konkretnych opcji (np. zmiana pracy, zakup mieszkania, system alarmowy czy kamery).\n"
            "- ALLOCATION: optymalny dobór podzbioru lub alokacja budżetu pod ograniczeniami (np. plecak, portfel inwestycyjny, harmonogramowanie).\n"
            "- DESIGN: synteza wielodźwigniowa złożonego systemu (np. całościowa reforma ochrony zdrowia, architektura instytucji z wieloma dźwigniami).\n"
            "- PARAMETER: kalibracja i optymalizacja zmiennych ciągłych (równania różniczkowe, optymalizacja numeryczna SciPy/HiGHS).\n"
            "- NOT_COMPUTABLE: pytania czysto metafizyczne, moralne, prognozy losowej przyszłości bez struktury decyzyjnej (np. 'czy bóg istnieje', 'jaki będzie kurs bitcoina za rok').\n\n"
            f"Zapytanie użytkownika:\n\"{query}\"\n"
        )
        try:
            res = await gateway.generate(
                system_instruction="Jesteś precyzyjnym klasyfikatorem problemów decyzyjnych. Zwracaj wyłącznie poprawny JSON.",
                user_content=prompt,
                purpose="classify_problem",
                response_schema=schema,
                temperature=0.1,
            )
            if res.parsed_json and isinstance(res.parsed_json, dict):
                p_class = str(res.parsed_json.get("problem_class", "CHOICE")).upper()
                if p_class in ("CHOICE", "ALLOCATION", "DESIGN", "PARAMETER", "NOT_COMPUTABLE"):
                    return ProblemClassification(
                        problem_class=p_class,
                        confidence=float(res.parsed_json.get("confidence", 0.9)),
                        reason=str(res.parsed_json.get("reason", "Klasyfikacja wygenerowana przez LLMGateway.")),
                        computable=bool(res.parsed_json.get("computable", p_class != "NOT_COMPUTABLE")),
                        reframe_suggestions=list(res.parsed_json.get("reframe_suggestions", [])),
                    )
        except Exception as e:
            logger.warning("LLMGateway classification failed, falling back to heuristic: %s", e)

    return heuristic_classify_problem(query, options_count)


def classify_problem_class(query: str, options_count: int = 0) -> str:
    """Classify problem into ProblemClass taxonomy."""
    return heuristic_classify_problem(query, options_count).problem_class


def _extract_linear_coeffs(node_id: str, nodes: dict[str, ExprNode]) -> dict[str, float]:
    """Helper to extract variable coefficients from safe expression trees."""
    coeffs: dict[str, float] = {}
    if not node_id or node_id not in nodes:
        return coeffs
    node = nodes[node_id]
    if node.op == "var":
        coeffs[str(node.value)] = 1.0
    elif node.op == "mul":
        c_val = 1.0
        v_name = None
        for child_id in node.children:
            child = nodes.get(child_id)
            if not child:
                continue
            if child.op == "const":
                c_val *= float(child.value or 0.0)
            elif child.op == "var":
                v_name = str(child.value)
        if v_name:
            coeffs[v_name] = c_val
    elif node.op in ("sum", "add"):
        for child_id in node.children:
            sub = _extract_linear_coeffs(child_id, nodes)
            for v, c in sub.items():
                coeffs[v] = coeffs.get(v, 0.0) + c
    return coeffs


def _extract_const_val(node_id: str | None, nodes: dict[str, ExprNode]) -> float:
    """Helper to extract constant numeric value from safe expression trees."""
    if not node_id or node_id not in nodes:
        return 0.0
    node = nodes[node_id]
    if node.op == "const":
        return float(node.value or 0.0)
    return 0.0


class ActiveInferenceOutcome(BaseModel):
    """Result of an active inference evaluation cycle."""
    status: Literal["PASS", "FAIL", "EXHAUSTED", "CLARIFICATION_REQUIRED"]
    reward_score: float = 0.0
    current_cycle: int = 0
    trace_id: str | None = None
    prediction_errors: list[str] = Field(default_factory=list)
    active_problem_ir: ProblemIR | None = None
    explanation: str = ""
    requires_reapproval: bool = False


class ActiveInferenceOrchestrator:
    """
    Brain-inspired cognitive engine coordinating Working Memory, Episodic Memory,
    Gemini/Fallback Reasoning Port, and the Independent Verifier.
    """

    def __init__(
        self,
        reasoning_port: CognitiveReasoningPort,
        episodic_repo: EpisodicMemoryRepository | None = None,
        budget: EnergyBudget | None = None,
    ) -> None:
        self.reasoning_port = reasoning_port
        self.episodic_repo = episodic_repo or EpisodicMemoryRepository()
        self.default_budget = budget or EnergyBudget()

    async def run_intake(
        self,
        session: AsyncSession,
        query: str,
        workspace: GlobalWorkspace | None = None,
        owner_id: str | None = None,
        workspace_id: str | None = None,
        problem_class_override: str | None = None,
    ) -> tuple[FormalizationResult, GlobalWorkspace]:
        """
        Execute unified Cognitive Perception pipeline (E1):
        Perception -> Computability -> Quality Gate -> Episodic Recall ->
        Hypothesis DecisionCase -> Research Plan -> Decision Matrix -> ProblemIR -> Sanity Check.
        """
        ws = workspace or GlobalWorkspace(goal=query, budget=self.default_budget.model_copy())
        fp = compute_problem_fingerprint(query)
        ws.energy_budget.consume_tokens(350)

        # 1. Classification & Computability assessment (D1 / N4)
        if problem_class_override:
            classification = ProblemClassification(
                problem_class=problem_class_override,
                confidence=1.0,
                reason="Klasa problemu jawnie wybrana przez użytkownika.",
                computable=problem_class_override != ProblemClass.NOT_COMPUTABLE.value,
            )
        else:
            classification = await classify_problem_class_async(query)

        if not classification.computable or classification.problem_class == ProblemClass.NOT_COMPUTABLE.value:
            ws.update_hypothesis(None, {"status": "not_computable"})
            nc_report = NotComputableReport(
                is_computable=False,
                reason=classification.reason or "Problem nie spełnia kryteriów obliczalności matematycznej.",
                reframe_suggestions=classification.reframe_suggestions or ["Zdefiniuj konkretne mierzalne warianty i kryteria wyboru."],
                suggested_computable_class=ProblemClass.CHOICE,
            )
            res = FormalizationResult(
                status="not_computable",
                raw_query=query,
                fingerprint=fp,
                problem_class=ProblemClass.NOT_COMPUTABLE.value,
                confidence=classification.confidence,
                not_computable_report=nc_report.model_dump(mode="json"),
                questions=nc_report.reframe_suggestions,
                explanation=f"Problem nie spełnia kryteriów obliczalności matematycznej: {nc_report.reason}",
                session_id=ws.session_id,
                metadata={"classification_reason": classification.reason},
            )
            return res, ws

        # 2. Input Quality Gate (aware of problem class)
        quality = assess_input_quality(query, problem_class=classification.problem_class)
        if quality.level != "sufficient":
            ws.update_hypothesis(None, {"status": "needs_clarification", "quality_level": quality.level})
            res = FormalizationResult(
                status="needs_clarification",
                raw_query=query,
                fingerprint=fp,
                problem_class=classification.problem_class,
                confidence=classification.confidence,
                input_quality=quality,
                questions=quality.suggestions,
                explanation=quality.reason,
                session_id=ws.session_id,
                metadata={"classification_reason": classification.reason},
            )
            return res, ws

        # 2b. Specialized DESIGN Synthesis Pathway (D2 / N5)
        # Synthesizes systemic architecture / policy dilemmas by decomposing into levers
        # with background research from web without requiring pre-specified user options.
        if classification.problem_class == ProblemClass.DESIGN.value:
            from backend.domain.cognitive.lever_decomposer import decompose_design_query_async
            from backend.infrastructure.web_research.search_adapter import WebResearchAdapter

            search_adapter = WebResearchAdapter()
            web_context_snippets: list[str] = []
            if search_adapter.is_available():
                ws.energy_budget.consume_search(2)
                try:
                    search_results = await search_adapter.search(query, max_results=3)
                    for sr in search_results:
                        web_context_snippets.append(f"[{sr.title}]({sr.url}): {sr.snippet}")
                except Exception as s_err:
                    logger.warning("Web search in design intake failed: %s", s_err)

            design_problem = await decompose_design_query_async(query)

            # Build compatible DecisionCase with options per lever for backward compatibility and case workspace
            case_options: list[Option] = []
            for lever in design_problem.levers:
                for opt in lever.options:
                    case_options.append(Option(
                        id=f"{lever.id}__{opt.id}",
                        title=f"{lever.name}: {opt.title}",
                        description=opt.description or "",
                    ))
            case_criteria: list[Criterion] = [
                Criterion(
                    id=c.id,
                    name=c.name,
                    direction=c.direction,
                    weight=c.weight,
                    unit=c.unit or "",
                )
                for c in design_problem.criteria
            ]
            case_score_matrix: dict[str, dict[str, Any]] = {}
            for opt in case_options:
                case_score_matrix[opt.id] = {}
                for crit in case_criteria:
                    from backend.domain.decision_case import ScoredValue
                    case_score_matrix[opt.id][crit.id] = ScoredValue(
                        value=7.0 if crit.direction == "maximize" else 3.0,
                        unit=crit.unit or "skala",
                        provenance="assumed",
                        source_ref="Wzorzec dziedzinowy analizy systemowej (wymaga potwierdzenia)",
                        confidence=0.75,
                    )

            case = DecisionCase(
                title=design_problem.title,
                context=query,
                options=case_options,
                criteria=case_criteria,
                score_matrix=case_score_matrix,
                input_quality=quality,
                unknowns=[],
                facts=[],
            )

            # Pre-populate score_matrix cells with baseline assumed values if empty
            for lev in design_problem.levers:
                if lev.id not in design_problem.score_matrix:
                    design_problem.score_matrix[lev.id] = {}
                for opt in lev.options:
                    if opt.id not in design_problem.score_matrix[lev.id]:
                        design_problem.score_matrix[lev.id][opt.id] = {}
                    for crit in design_problem.criteria:
                        if crit.id not in design_problem.score_matrix[lev.id][opt.id]:
                            from backend.domain.decision_case import ScoredValue
                            design_problem.score_matrix[lev.id][opt.id][crit.id] = ScoredValue(
                                value=7.0 if crit.direction == "maximize" else 3.0,
                                unit=crit.unit or "skala",
                                provenance="assumed",
                                source_ref="Wzorzec dziedzinowy analizy systemowej (wymaga potwierdzenia)",
                                confidence=0.75,
                            )

            formalization = FormalizationResult(
                status="ready_for_review",
                raw_query=query,
                fingerprint=fp,
                problem_class=classification.problem_class,
                confidence=classification.confidence,
                decision_case=case,
                design_problem=design_problem.model_dump(mode="json"),
                explanation=design_problem.description,
                session_id=ws.session_id,
                metadata={
                    "classification_reason": classification.reason,
                    "web_sources_count": len(web_context_snippets),
                },
            )
            ws.update_hypothesis(None, {"status": "ready_for_review", "class": "DESIGN"})
            return formalization, ws

        # 3. Hippocampal recall of historical analogies with tenant isolation (A18)
        analogies = await self.episodic_repo.recall_analogies(
            session,
            fingerprint=fp,
            limit=3,
            owner_id=owner_id,
            workspace_id=workspace_id,
        )

        # 4. Hypothesis formulation as DecisionCase (E1)
        from backend.domain.llm_advisor import LLMAdvisor
        advisor = LLMAdvisor()
        case = await advisor.analyze_case_async(query)
        case.input_quality = quality
        problem_class_name = problem_class_override or classification.problem_class

        # 5. Research planning for missing data/sources (C3)
        from backend.domain.evidence.planner import ResearchPlanner
        research_planner = ResearchPlanner()
        planned_queries = research_planner.identify_missing_parameters(case)
        research_queries_json = [q.model_dump(mode="json") for q in planned_queries]
        ws.energy_budget.consume_search(len(planned_queries))


        # 6. Break-Even point calculation (B1)
        if case.options and case.criteria and not case.break_even_point:
            from backend.domain.decision_matrix import calculate_analytical_break_even
            be = calculate_analytical_break_even(case)
            if be:
                case.break_even_point = be.summary_pl

        # 7. Formalize query into ProblemIR via Reasoning Port
        formalization = await self.reasoning_port.formalize_query(
            query=query,
            analogies=analogies,
            error_context=ws.memory.prediction_errors if ws.memory.prediction_errors else None,
        )

        formalization.decision_case = case
        formalization.problem_class = problem_class_name
        formalization.confidence = classification.confidence
        if classification.reason:
            formalization.metadata["classification_reason"] = classification.reason
        formalization.input_quality = quality
        formalization.research_queries = research_queries_json
        formalization.break_even_point = case.break_even_point
        formalization.session_id = ws.session_id

        if formalization.status == "needs_clarification" or formalization.problem_ir is None:
            ws.update_hypothesis(None, {"status": "needs_clarification"})
            return formalization, ws

        # 8. Pre-solver constraint sanity check
        sanity = check_constraints_sanity(formalization.problem_ir)
        if not sanity.passed:
            for err in sanity.errors:
                ws.register_prediction_error(f"Sanity Check Failure: {err}")

            if not ws.energy_budget.is_exhausted() and ws.energy_budget.next_cycle():
                logger.info(
                    "Sanity check caught contradictions. Entering internal reflection cycle %d.",
                    ws.energy_budget.current_cycle,
                )
                return await self.run_intake(
                    session=session,
                    query=query,
                    workspace=ws,
                    owner_id=owner_id,
                    workspace_id=workspace_id,
                )
            else:
                formalization.questions.extend(sanity.errors)
                formalization.status = "needs_clarification"
                formalization.explanation += " Wykryto wewnętrzne sprzeczności w ograniczeniach."

        if formalization.problem_ir is not None:
            ir = formalization.problem_ir
            nodes = ir.expressions.nodes
            bin_vars = [v.name for v in ir.variables if v.domain == VariableDomain.BINARY] or [v.name for v in ir.variables]
            eq_constrs = []
            ineq_constrs = []
            for c in ir.constraints:
                lhs_coeffs = _extract_linear_coeffs(c.lhs_expression_id, nodes)
                rhs_val = _extract_const_val(c.rhs_expression_id, nodes)
                c_dto = {"lhs": lhs_coeffs, "rhs": rhs_val}
                if c.type == ConstraintType.EQUALITY:
                    eq_constrs.append(c_dto)
                else:
                    ineq_constrs.append(c_dto)

            obj_coeffs: dict[str, float] = {}
            if ir.objectives:
                obj_coeffs = _extract_linear_coeffs(ir.objectives[0].expression_id, nodes)

            formalization.formalized = {
                "description_raw": formalization.raw_query or query,
                "description_formalised": formalization.explanation or query,
                "binary_variables": bin_vars,
                "objective_direction": "maximize" if (ir.objectives and ir.objectives[0].direction == ObjectiveDirection.MAXIMIZE) else "minimize",
                "objective_coefficients": obj_coeffs,
                "equality_constraints": eq_constrs,
                "inequality_constraints": ineq_constrs,
                "assumptions": [a.statement for a in ir.assumptions],
                "missing_information": [m.description for m in ir.missing_information],
                "identified_archetype": formalization.problem_class,
                "break_even_point": formalization.break_even_point,
            }

        ws.update_hypothesis(formalization.problem_ir, {"status": formalization.status})
        return formalization, ws

    async def process_verification_feedback(
        self,
        session: AsyncSession,
        workspace: GlobalWorkspace,
        verifier_report: VerificationReport,
        raw_query: str,
        winning_solver: str = "cpsat",
        consent: bool = True,
        anonymize: bool = False,
    ) -> ActiveInferenceOutcome:
        """
        Active Inference Error Minimization Loop (Stage 5-6):
        - If Verifier passes (PASS): consolidates trace (E5).
        - If Verifier fails (FAIL): treats violations as Prediction Errors, consumes cycle,
          and adapts hypothesis.
        - MANDATORY DEC-002: Any revised ProblemIR generated MUST be unapproved (approved=False, approved_at=None)
          and require explicit human re-approval before running any solver!
        """
        is_pass = verifier_report.verdict == Verdict.PASS or (
            verifier_report.feasible and verifier_report.verdict != Verdict.FAIL
        )

        cycle = workspace.energy_budget.current_cycle

        if is_pass:
            # Reward score: 1.0 for zero reflection cycles, decaying gracefully
            reward = 1.0 if cycle == 0 else max(0.5, 1.0 - (cycle * 0.15))
            fp = compute_problem_fingerprint(raw_query)
            trace_id: str | None = None

            # E5: Consent-gated consolidation
            if consent:
                ir_dict = (
                    workspace.memory.active_hypothesis.model_dump(mode="json")
                    if workspace.memory.active_hypothesis
                    else {}
                )
                user_query_to_save = "[ANONYMIZED_STRUCTURAL_QUERY]" if anonymize else raw_query
                trace_id = await self.episodic_repo.consolidate_trace(
                    session=session,
                    trace_data={
                        "problem_fingerprint": fp,
                        "raw_user_query": user_query_to_save,
                        "successful_ir_json": ir_dict,
                        "winning_solver": winning_solver,
                        "penalty_multipliers": {},
                        "reward_score": reward,
                        "lessons_learned": f"Zbieżność osiągnięta w cyklu {cycle} przy weryfikacji {verifier_report.verdict.value}.",
                    },
                )

            return ActiveInferenceOutcome(
                status="PASS",
                reward_score=reward,
                current_cycle=cycle,
                trace_id=trace_id,
                active_problem_ir=workspace.memory.active_hypothesis,
                explanation="Model pomyślnie zweryfikowany przez niezależny weryfikator.",
                requires_reapproval=False,
            )

        # Verification Failed: compute prediction errors
        error_signals: list[str] = [f"Verifier Verdict: {verifier_report.verdict.value} ({verifier_report.verdict_reason})"]
        for cr in verifier_report.constraint_results:
            if not cr.satisfied:
                error_signals.append(
                    f"Naruszone ograniczenie {cr.constraint_id} (mag={cr.violation_magnitude}, note={cr.note})"
                )
        for dv in verifier_report.domain_violations:
            error_signals.append(f"Naruszenie dziedziny zmiennej {dv}")
        if verifier_report.numerical_residual is not None and verifier_report.numerical_residual > 1e-4:
            error_signals.append(f"Residuum numeryczne przekracza tolerancję: {verifier_report.numerical_residual:.6e}")

        for sig in error_signals:
            workspace.register_prediction_error(sig)

        # Check energy exhaustion
        if workspace.energy_budget.is_exhausted() or not workspace.energy_budget.next_cycle():
            reason = workspace.energy_budget.get_exhaustion_reason() or "Przekroczono limit energii/cykli."
            logger.warning("Active inference metabolic budget depleted: %s", reason)
            return ActiveInferenceOutcome(
                status="EXHAUSTED",
                reward_score=0.0,
                current_cycle=workspace.energy_budget.current_cycle,
                prediction_errors=list(workspace.memory.prediction_errors),
                active_problem_ir=workspace.memory.active_hypothesis,
                explanation=f"{reason} Sugestia: {'; '.join(workspace.energy_budget.suggest_simplifications())}",
                requires_reapproval=False,
            )

        # Free Energy Minimization: generate refined hypothesis with error context
        fp = compute_problem_fingerprint(raw_query)
        analogies = await self.episodic_repo.recall_analogies(session, fingerprint=fp, limit=2)
        revised_res = await self.reasoning_port.formalize_query(
            query=raw_query,
            analogies=analogies,
            error_context=workspace.memory.prediction_errors,
        )
        workspace.energy_budget.consume_tokens(300)

        if revised_res.problem_ir is not None:
            # DEC-002: Revised hypothesis MUST be unapproved and require human re-approval!
            revised_ir = revised_res.problem_ir
            revised_ir.approved = False
            revised_ir.approved_at = None
            workspace.update_hypothesis(revised_ir, {"status": "revised_hypothesis_unapproved"})
            return ActiveInferenceOutcome(
                status="FAIL",
                reward_score=0.2,
                current_cycle=workspace.energy_budget.current_cycle,
                prediction_errors=list(workspace.memory.prediction_errors),
                active_problem_ir=revised_ir,
                explanation="Zarejestrowano błąd weryfikatora. Wygenerowano zaktualizowaną hipotezę ProblemIR wymagającą zatwierdzenia przez użytkownika.",
                requires_reapproval=True,
            )

        return ActiveInferenceOutcome(
            status="CLARIFICATION_REQUIRED",
            reward_score=0.0,
            current_cycle=workspace.energy_budget.current_cycle,
            prediction_errors=list(workspace.memory.prediction_errors),
            active_problem_ir=None,
            explanation="Autorefleksja wymaga doprecyzowania od użytkownika.",
            requires_reapproval=False,
        )
