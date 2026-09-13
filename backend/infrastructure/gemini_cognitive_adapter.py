"""
YourQuantum — Gemini Cognitive Adapter (Infrastructure Layer)
Integrates Gemini 2.5 Flash API for cognitive problem formalization with:
- Strict JSON structured output
- Few-Shot Cognitive Exemplars injected from episodic memory
- Prediction Error reflex loop prompts
- Seamless deterministic offline fallback on missing key, 429 rate limit, or network failure.
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

import httpx

from backend.domain.cognitive.cognitive_port import CognitiveReasoningPort, FormalizationResult
from backend.domain.cognitive.ir_builder import build_problem_ir
from backend.domain.problem_ir import ProblemIR

logger = logging.getLogger(__name__)

GEMINI_API_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"


_DEFAULT_KEY = object()


class GeminiCognitiveAdapter(CognitiveReasoningPort):
    """
    Adapter communicating with Google Gemini API to formalize unstructured problems
    into mathematically rigorous ProblemIR contracts with automated offline fallback.
    """

    def __init__(
        self,
        api_key: str | None | object = _DEFAULT_KEY,
        model: str | None = None,
        timeout: float = 15.0,
    ) -> None:
        if api_key is _DEFAULT_KEY:
            self.api_key = os.getenv("GEMINI_API_KEY")
        else:
            self.api_key = api_key
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.timeout = timeout

    async def formalize_query(
        self,
        query: str,
        analogies: list[dict[str, Any]] | None = None,
        error_context: list[str] | None = None,
    ) -> FormalizationResult:
        """
        Attempt cognitive formalization via Gemini API.
        Falls back to local deterministic heuristic if API key is missing or request fails.
        """
        cleaned_query = query.strip()
        if not cleaned_query:
            return FormalizationResult(
                status="needs_clarification",
                problem_ir=None,
                questions=["Podaj treść problemu decyzyjnego lub optymalizacyjnego."],
                explanation="Zapytanie użytkownika jest puste.",
                raw_query="",
                confidence=0.0,
            )

        if not self.api_key:
            logger.info("GEMINI_API_KEY is not configured. Utilizing deterministic offline fallback.")
            return self._deterministic_fallback(cleaned_query, error_context)

        try:
            return await self._call_gemini_api(cleaned_query, analogies, error_context)
        except Exception as e:
            logger.warning("Gemini API call failed (%s). Activating deterministic fallback.", e)
            return self._deterministic_fallback(cleaned_query, error_context)

    async def _call_gemini_api(
        self,
        query: str,
        analogies: list[dict[str, Any]] | None,
        error_context: list[str] | None,
    ) -> FormalizationResult:
        """Execute async HTTP request to Gemini REST API enforcing JSON schema."""
        url = GEMINI_API_URL_TEMPLATE.format(model=self.model, key=self.api_key)

        schema_format = (
            "Wymagany format JSON:\n"
            "{\n"
            '  "status": "ready_for_review",\n'
            '  "explanation": "Zwięzłe podsumowanie problemu",\n'
            '  "questions": [],\n'
            '  "variables": [\n'
            '    {"id": "var_a", "name": "Projekt A", "domain": "binary"}\n'
            "  ],\n"
            '  "objective": {\n'
            '    "direction": "maximize",\n'
            '    "coefficients": {"var_a": 30.0}\n'
            "  },\n"
            '  "constraints": [\n'
            "    {\n"
            '      "id": "c_budget",\n'
            '      "type": "inequality_le",\n'
            '      "lhs_terms": {"var_a": 20.0},\n'
            '      "rhs": 50.0,\n'
            '      "description": "Limit budżetu"\n'
            "    }\n"
            "  ],\n"
            '  "penalty_multipliers": {"c_budget": 100.0}\n'
            "}"
        )

        system_instruction = (
            "Jesteś precyzyjnym mózgiem kognitywnym w systemie YourQuantum. "
            "Twoim jedynym zadaniem jest sformalizowanie dylematu decyzyjnego użytkownika do postaci ProblemIR. "
            "ZASADY NIENEGOCJOWALNE:\n"
            "1. LLM output != solver result. Nigdy nie wyznaczaj wartości zmiennych decyzyjnych ani nie twórz fikcyjnych dowodów.\n"
            "2. Zidentyfikuj zmienne decyzyjne, funkcję celu (maksymalizacja lub minimalizacja) oraz twarde ograniczenia (nierówności liniowe).\n"
            f"3. Zwróć wyłącznie prawidłowy dokument JSON ściśle według schematu:\n{schema_format}"
        )

        from backend.infrastructure.llm_gateway import LLMGateway

        exemplar_prompts: list[dict[str, Any]] = []
        if analogies:
            for ex in analogies:
                exemplar_prompts.append({
                    "role": "user",
                    "parts": [{"text": f"Przykład historyczny:\nZapytanie: {ex.get('raw_user_query')}"}],
                })
                exemplar_prompts.append({
                    "role": "model",
                    "parts": [{"text": json.dumps(ex.get("successful_ir_json", {}), ensure_ascii=False)}],
                })

        user_content = f"Sformalizuj poniższe zadanie decyzyjne:\n\n\"{query}\""
        if error_context:
            user_content += (
                f"\n\nUWAGA: Poprzednia hipoteza została odrzucona przez Independent Verifier z błędami predykcji:\n"
                + "\n".join(f"- {err}" for err in error_context)
                + "\nSkoryguj definicję ograniczeń lub wag kar, aby wyeliminować powyższe błędy."
            )

        gateway = LLMGateway(api_key=self.api_key, model=self.model, timeout=self.timeout)
        response = await gateway.generate(
            system_instruction=system_instruction,
            user_content=user_content,
            purpose="cognitive_formalization",
            few_shots=exemplar_prompts,
        )

        if response.is_offline or response.parsed_json is None:
            raise ValueError(f"Gemini gateway error: {response.error or 'empty response'}")

        return self._parse_json_to_formalization_result(query, response.parsed_json, error_context)

    def _parse_json_to_formalization_result(
        self,
        query: str,
        parsed: dict[str, Any],
        error_context: list[str] | None,
    ) -> FormalizationResult:
        """Parse structured model output into FormalizationResult containing ProblemIR."""
        status = parsed.get("status", "ready_for_review")
        explanation = parsed.get("explanation", "Kognitywna formalizacja problemu.")
        questions = parsed.get("questions", [])

        vars_spec = parsed.get("variables") or parsed.get("decision_variables") or []
        norm_vars: list[dict[str, Any]] = []
        for idx, v in enumerate(vars_spec):
            if isinstance(v, str):
                norm_vars.append({"id": v, "name": v, "domain": "binary"})
            elif isinstance(v, dict):
                vid = str(v.get("id") or v.get("name") or f"var_{idx+1}")
                dom = str(v.get("domain") or v.get("type") or "binary")
                norm_vars.append({
                    "id": vid,
                    "name": str(v.get("name") or vid),
                    "domain": dom,
                    "lower_bound": v.get("lower_bound"),
                    "upper_bound": v.get("upper_bound"),
                })

        if status == "needs_clarification" or not norm_vars:
            return FormalizationResult(
                status="needs_clarification",
                problem_ir=None,
                questions=questions or ["Wymagane jest doprecyzowanie celów i ograniczeń."],
                explanation=explanation,
                raw_query=query,
                confidence=0.5,
            )

        # Objective normalization
        raw_obj = parsed.get("objective") or parsed.get("objective_function") or {}
        obj_direction = str(raw_obj.get("direction") or raw_obj.get("type") or "maximize")
        obj_coeffs = dict(raw_obj.get("coefficients", {}))
        if not obj_coeffs and "expression" in raw_obj:
            for m in re.finditer(r"([+-]?\s*\d+(?:\.\d+)?)\s*\*\s*([a-zA-Z0-9_]+)", str(raw_obj["expression"])):
                c_val = float(m.group(1).replace(" ", ""))
                v_name = m.group(2)
                obj_coeffs[v_name] = c_val
        obj_spec = {"direction": obj_direction, "coefficients": obj_coeffs}

        # Constraints normalization
        raw_cons = parsed.get("constraints", [])
        norm_cons: list[dict[str, Any]] = []
        for idx, c in enumerate(raw_cons):
            if isinstance(c, dict):
                cid = c.get("id") or f"c_{idx+1}"
                ctype = c.get("type", "inequality_le")
                lhs_terms = dict(c.get("lhs_terms", {}))
                rhs = c.get("rhs")
                if not lhs_terms and "expression" in c:
                    expr = str(c["expression"])
                    if "<=" in expr:
                        lhs_part, rhs_part = expr.split("<=", 1)
                        ctype = "inequality_le"
                        r_nums = re.findall(r"\d+(?:\.\d+)?", rhs_part)
                        rhs = float(r_nums[0]) if r_nums else 0.0
                    elif ">=" in expr:
                        lhs_part, rhs_part = expr.split(">=", 1)
                        ctype = "inequality_ge"
                        r_nums = re.findall(r"\d+(?:\.\d+)?", rhs_part)
                        rhs = float(r_nums[0]) if r_nums else 0.0
                    elif "==" in expr or "=" in expr:
                        lhs_part, rhs_part = re.split(r"==?", expr, maxsplit=1)
                        ctype = "equality"
                        r_nums = re.findall(r"\d+(?:\.\d+)?", rhs_part)
                        rhs = float(r_nums[0]) if r_nums else 0.0
                    else:
                        lhs_part = expr
                        rhs = 0.0

                    for m in re.finditer(r"([+-]?\s*\d+(?:\.\d+)?)\s*\*\s*([a-zA-Z0-9_]+)", lhs_part):
                        c_val = float(m.group(1).replace(" ", ""))
                        v_name = m.group(2)
                        lhs_terms[v_name] = c_val

                norm_cons.append({
                    "id": cid,
                    "type": ctype,
                    "lhs_terms": lhs_terms,
                    "rhs": float(rhs if rhs is not None else 0.0),
                    "hard": c.get("hard", True),
                    "description": c.get("description", f"Ograniczenie {cid}"),
                })

        penalties = parsed.get("penalty_multipliers", {})

        ir = build_problem_ir(
            raw_query=query,
            variables_spec=norm_vars,
            objective_spec=obj_spec,
            constraints_spec=norm_cons,
            formalised_description=explanation,
        )

        return FormalizationResult(
            status="ready_for_review",
            problem_ir=ir,
            questions=[],
            explanation=explanation,
            raw_query=query,
            fingerprint=f"gemini_vars_{len(norm_vars)}_cons_{len(norm_cons)}",
            confidence=0.95,
            penalty_multipliers=penalties,
        )

    def _deterministic_fallback(
        self,
        query: str,
        error_context: list[str] | None = None,
    ) -> FormalizationResult:
        """
        Local deterministic heuristic formalizer that guarantees reliable, honest operation
        without fabricating missing numbers or automatically loosening user constraints.
        """
        lower = query.lower()

        penalties: dict[str, float] = {}
        if error_context:
            for err in error_context:
                err_lower = err.lower()
                if "c_budget" in err_lower or "budget" in err_lower or "budzet" in err_lower:
                    penalties["c_budget"] = 2.5

        # Look for explicit budget / capacity
        budget_match = re.search(
            r"(?:budż[a-z]*|budz[a-z]*|pojemnoś[a-z]*|pojemnosc[a-z]*|udźwig[a-z]*|limit[a-z]*|maksymalnie|max)\s*(?:=|:|\sto\s|\swynosi\s)?\s*(\d+(?:\.\d+)?)",
            lower,
        )
        has_explicit_budget = budget_match is not None
        limit_val = float(budget_match.group(1)) if budget_match else None

        # Look for explicit options / projects
        named_letters = re.findall(r"\b([A-Z])\b", query)
        valid_letters = [ltr for ltr in named_letters if ltr not in ["W", "Z", "I", "O", "A", "U"] or len(named_letters) > 1]
        unique_letters = list(dict.fromkeys(valid_letters)) if valid_letters else []

        # Look for lists of profits and costs in query
        profits_match = re.search(r"(?:zysk[a-z]*|wartoś[a-z]*|wartosc[a-z]*)\s*[:=]?\s*([0-9\s,\.]+)", lower)
        costs_match = re.search(r"(?:koszt[a-z]*|wag[a-z]*|cen[a-z]*)\s*[:=]?\s*([0-9\s,\.]+)", lower)

        extracted_profits: list[float] = []
        extracted_costs: list[float] = []
        if profits_match:
            extracted_profits = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", profits_match.group(1))]
        if costs_match:
            extracted_costs = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", costs_match.group(1))]

        # If data is incomplete or missing, DO NOT invent values
        missing_items: list[str] = []
        if not unique_letters and len(extracted_profits) < 2:
            missing_items.append("konkretne warianty decyzyjne do wyboru")
        if not extracted_profits and not extracted_costs:
            missing_items.append("wartości (zyski, oceny lub korzyści) dla każdego wariantu")
        if not extracted_costs and not has_explicit_budget:
            missing_items.append("koszty poszczególnych opcji oraz limit budżetowy / zasobów")
        elif not has_explicit_budget:
            missing_items.append("maksymalny limit budżetu / udźwigu")

        if missing_items:
            questions = [f"Podaj {item}." for item in missing_items]
            return FormalizationResult(
                status="needs_clarification",
                problem_ir=None,
                questions=questions,
                explanation=f"Do precyzyjnego sformułowania problemu brakuje danych liczbowych: {', '.join(missing_items)}. System YourQuantum nie fabrykuje brakujących liczb.",
                raw_query=query,
                confidence=0.3,
            )

        # If we have extracted numbers from text
        n_items = min(len(extracted_profits), len(extracted_costs))
        if unique_letters and len(unique_letters) >= n_items and n_items > 0:
            item_labels = unique_letters[:n_items]
        else:
            item_labels = [f"{i+1}" for i in range(n_items)]

        variables_spec: list[dict[str, Any]] = []
        obj_coeffs: dict[str, float] = {}
        constraint_terms: dict[str, float] = {}

        for idx, lbl in enumerate(item_labels):
            vid = f"var_{lbl.lower()}"
            variables_spec.append({
                "id": vid,
                "name": f"Wariant {lbl}",
                "domain": "binary",
                "lower_bound": 0,
                "upper_bound": 1,
            })
            obj_coeffs[vid] = extracted_profits[idx]
            constraint_terms[vid] = extracted_costs[idx]

        constraints_spec: list[dict[str, Any]] = []
        if limit_val is not None:
            constraints_spec.append({
                "id": "c_budget",
                "type": "inequality_le",
                "lhs_terms": constraint_terms,
                "rhs": limit_val,
                "hard": True,
                "description": f"Ograniczenie budżetu do {limit_val}",
            })

        # Check for mutual exclusion in text
        if any(w in lower for w in ["wyklucz", "albo", "tylko jeden"]):
            if len(variables_spec) >= 2:
                v1 = variables_spec[0]["id"]
                v2 = variables_spec[1]["id"]
                constraints_spec.append({
                    "id": "c_mutex",
                    "type": "inequality_le",
                    "lhs_terms": {v1: 1.0, v2: 1.0},
                    "rhs": 1.0,
                    "hard": True,
                    "description": f"Wykluczenie wzajemne {v1} oraz {v2}",
                })

        ir = build_problem_ir(
            raw_query=query,
            variables_spec=variables_spec,
            objective_spec={"direction": "maximize", "coefficients": obj_coeffs},
            constraints_spec=constraints_spec,
            formalised_description=f"Deterministyczna formalizacja regułowa na podstawie liczb z zapytania: {len(variables_spec)} zmiennych, {len(constraints_spec)} ograniczeń.",
        )

        return FormalizationResult(
            status="ready_for_review",
            problem_ir=ir,
            questions=[],
            explanation="Problem sformalizowano regułowo wyłącznie w oparciu o liczby podane przez użytkownika.",
            raw_query=query,
            fingerprint=f"offline_v{len(variables_spec)}_c{len(constraints_spec)}",
            confidence=0.85,
            penalty_multipliers={"c_budget": 100.0} if constraints_spec else {},
        )
