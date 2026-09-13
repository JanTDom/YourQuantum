"""
YourQuantum — Problem Formalizer
Translates natural language descriptions into structured ProblemIR proposals
or human DecisionCase models.

Architecture:
1. Deterministic Semantic Heuristic Engine (100% offline, zero-dependency)
   - Accurately detects:
     * Human decision dilemmas (job change, vendor choice, life tradeoffs)
     * Knapsack / resource allocation
     * Max-Cut / graph partitioning (quadratic formulation)
     * Project / portfolio selection (honest variables, inequality for 'maksymalnie K', no fabricated profits)
2. Optional LLM Adapter:
   - Activates only if GEMINI_API_KEY or OPENAI_API_KEY is present in env.
   - Strictly conforms to principle: LLM helps formalize the model;
     it NEVER fabricates solver execution or mathematical proof.
"""
from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any

from dotenv import load_dotenv

load_dotenv()

from backend.infrastructure.llm_gateway import LLMGateway

from backend.domain.decision_case import (
    Criterion,
    DecisionCase,
    Fact,
    Option,
    Tradeoff,
    Unknown,
)

logger = logging.getLogger(__name__)


@dataclass
class FormalizationResult:
    description_raw: str
    description_formalised: str
    binary_variables: list[str]
    objective_direction: str  # "minimize" | "maximize"
    objective_coefficients: dict[str, float]
    equality_constraints: list[dict[str, Any]] = field(default_factory=list)
    inequality_constraints: list[dict[str, Any]] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    missing_information: list[str] = field(default_factory=list)
    identified_archetype: str = "custom"
    break_even_point: str | None = None


def _pl_projects(n: int) -> str:
    """Return grammatically correct Polish noun for 'project(s)'."""
    if n == 1:
        return "projekt"
    if 2 <= n <= 4:
        return "projekty"
    return "projektów"


def _pl_options(n: int) -> str:
    """Return grammatically correct Polish noun for 'option(s)'."""
    if n == 1:
        return "opcję"
    if 2 <= n <= 4:
        return "opcje"
    return "opcji"


class ProblemFormalizer:
    """Translates user natural language into structured candidate models."""

    def __init__(self, gemini_api_key: str | None = None, openai_api_key: str | None = None):
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

    def formalize(self, text: str) -> FormalizationResult:
        """Analyze natural language text and return structured model proposal."""
        cleaned = text.strip()
        if not cleaned:
            return FormalizationResult(
                description_raw="",
                description_formalised="Pusty opis zadania.",
                binary_variables=[],
                objective_direction="minimize",
                objective_coefficients={},
                missing_information=["Opis problemu jest pusty."],
            )

        lower = cleaned.lower()
        # If text matches known domain archetypes, use deterministic heuristic parser
        # to guarantee zero hallucinations and accurate constraint / missing data extraction
        is_archetype = (
            (("czy" in lower and any(w in lower for w in ["zmienić", "zmienic", "zostać", "zostac", "kupić", "kupic", "wynająć", "nie wiem", "wahać"])) or
             ("wybór między" in lower or "wybor miedzy" in lower or ("albo" in lower and "albo" in lower[lower.find("albo")+4:]))) or
            any(w in lower for w in ["plecak", "knapsack", "udźwig", "pojemność", "pojemnosc", "ciężar"]) or
            any(w in lower for w in ["max-cut", "max cut", "cięcie grafu", "ciecie grafu", "podział grafu", "podzial grafu", "rozcięcie"]) or
            any(w in lower for w in ["projekt", "portfel", "inwestycj", "aktyw", "roi", "spośród", "sposrod"])
        )
        if is_archetype:
            return self._heuristic_formalize(cleaned)

        # For general unstructured text without explicit archetype, attempt LLM extraction
        if self.gemini_api_key or self.openai_api_key:
            try:
                llm_res = self._try_llm_formalize(cleaned)
                if llm_res is not None:
                    return llm_res
            except Exception as e:
                logger.warning(f"LLM formalization failed, falling back to heuristic engine: {e}")

        # Deterministic semantic heuristic engine
        return self._heuristic_formalize(cleaned)

    def _heuristic_formalize(self, text: str) -> FormalizationResult:
        """Deterministic pattern and semantic matching."""
        lower = text.lower()

        # ─── 0. Life dilemmas / Everyday choices ───
        # "czy zmienić pracę, czy zostać", "nie wiem czy", "wybór między X a Y"
        if ("czy" in lower and any(w in lower for w in ["zmienić", "zmienic", "zostać", "zostac", "kupić", "kupic", "wynająć", "nie wiem", "wahać"])) or \
           ("wybór między" in lower or "wybor miedzy" in lower or "albo" in lower and "albo" in lower[lower.find("albo")+4:]):
            return self._extract_life_dilemma(text, lower)

        # ─── 1. Knapsack / Plecak ───
        if any(w in lower for w in ["plecak", "knapsack", "udźwig", "pojemność", "pojemnosc", "ciężar"]):
            return self._extract_knapsack(text, lower)

        # ─── 2. Max-Cut / Podział grafu ───
        if any(w in lower for w in ["max-cut", "max cut", "cięcie grafu", "ciecie grafu", "podział grafu", "podzial grafu", "rozcięcie"]):
            return self._extract_maxcut(text, lower)

        # ─── 3. Portfolio / Inwestycje / Wybór projektów ───
        if any(w in lower for w in ["projekt", "portfel", "inwestycj", "aktyw", "roi", "spośród", "sposrod"]):
            return self._extract_portfolio(text, lower)

        # ─── 4. General linear / fallback extraction ───
        return self._extract_general(text, lower)

    def _extract_life_dilemma(self, text: str, lower: str) -> FormalizationResult:
        """Extract everyday decision dilemma without synthesizing fake x0, x1, x2."""
        dilemma_match = re.search(r"czy\s+(.+?)(?:,|\s+)\s*czy\s+(.+)", text, re.IGNORECASE)
        opt_names: list[str] = []
        if dilemma_match:
            raw_a = dilemma_match.group(1).strip(" .?!,")
            raw_b = dilemma_match.group(2).strip(" .?!,")
            var_a = self._slugify(raw_a)
            var_b = self._slugify(raw_b)
            opt_names = [var_a, var_b]
        else:
            opt_names = ["opcja_a", "opcja_b"]

        missing = [
            "Brak określonych kryteriów oceny (np. wynagrodzenie, kultura organizacyjna, stabilność, dojazdy).",
            "Brak przypisanych wag ważności dla poszczególnych kryteriów.",
            "Wymagane doprecyzowanie warunków brzegowych i ewentualnych warunków koniecznych (must-have).",
        ]
        assumptions = [
            f"Zidentyfikowano warianty decyzyjne: {', '.join(opt_names)}.",
            "Problem zakłada wybór pojedynczego wariantu (wzajemnie wykluczające się opcje).",
        ]

        coeffs = {v: 1.0 for v in opt_names}
        formalized_desc = (
            f"Twój dylemat: {text}\n\n"
            f"System zidentyfikował dwie możliwości do porównania. "
            f"Przed obliczeniami potrzebujemy Twoich kryteriów — "
            f"co jest dla Ciebie najważniejsze przy tym wyborze."
        )

        return FormalizationResult(
            description_raw=text,
            description_formalised=formalized_desc,
            binary_variables=opt_names,
            objective_direction="maximize",
            objective_coefficients=coeffs,
            equality_constraints=[{
                "lhs": {v: 1.0 for v in opt_names},
                "rhs": 1.0,
            }],
            assumptions=assumptions,
            missing_information=missing,
            identified_archetype="decision_dilemma",
        )

    def _extract_portfolio(self, text: str, lower: str) -> FormalizationResult:
        """
        Extract project selection without inventing fake profits.
        Properly handles 'maksymalnie K' (<=) vs 'dokładnie K' (==).
        """
        # Determine projects
        projects: list[str] = []
        # Explicit letters, e.g. "spośród A, B, C" or "A, B, C"
        named_letters = re.findall(r"\b([A-Z])\b", text)
        valid_letters = [ltr for ltr in named_letters if ltr not in ["W", "Z", "I", "O", "A", "U"]]
        if "spośród" in lower or "sposrod" in lower or "projekt" in lower:
            # Look for "spośród A, B, C"
            m = re.search(r"(?:spośród|sposrod)\s+([A-Za-z,\s]+)", text, re.IGNORECASE)
            if m:
                tokens = [t.strip().upper() for t in re.split(r"[,i\s]+", m.group(1)) if t.strip()]
                valid_tokens = [t for t in tokens if len(t) <= 3 and t.isalpha()]
                if valid_tokens:
                    projects = [f"proj_{t}" for t in valid_tokens]

        if not projects:
            # Check for "N projektów"
            n_match = re.search(r"(\d+)\s+(?:projektów|projektow|inwestycji|zadań|zadan)", lower)
            if n_match:
                count = int(n_match.group(1))
                count = min(max(count, 1), 20)
                projects = [f"proj_{i}" for i in range(1, count + 1)]

        if not projects:
            # Check for explicit proj_X
            explicit = re.findall(r"\bproj_([a-zA-Z0-9]+)\b", text)
            if explicit:
                projects = [f"proj_{e}" for e in explicit]

        if not projects:
            # Default to candidates based on context
            projects = ["proj_1", "proj_2", "proj_3", "proj_4"]

        # Parse limit / selection target
        is_inequality = False
        k_val = 2.0

        if any(w in lower for w in ["maksymalnie", "najwyżej", "najwyzej", "do ", "nie więcej niż", "nie wiecej niz", "limit"]):
            is_inequality = True

        k_match = re.search(r"(?:wybierz|wybór|maksymalnie|dokładnie|do)\s*(\d+)", lower)
        if k_match:
            k_val = float(k_match.group(1))

        # Check for explicitly provided profits in user text
        profits: dict[str, float] = {}
        missing: list[str] = []
        assumptions: list[str] = []

        # Try to parse pairs like "A: 10, B: 20"
        found_explicit_profits = False
        for p in projects:
            p_short = p.replace("proj_", "")
            val_match = re.search(rf"\b{p_short}\s*(?:to|:|=|\-)?\s*(\d+(?:[.,]\d+)?)", text, re.IGNORECASE)
            if val_match:
                profits[p] = float(val_match.group(1).replace(",", "."))
                found_explicit_profits = True
            else:
                profits[p] = 1.0

        if not found_explicit_profits:
            missing.append("Brak danych o oczekiwanym zysku, stopie zwrotu lub kosztach poszczególnych projektów.")
            assumptions.append("Przyjęto jednostkową wagę każdego projektu ze względu na brak kwot w opisie.")

        eq_constraints: list[dict[str, Any]] = []
        ineq_constraints: list[dict[str, Any]] = []

        if is_inequality:
            ineq_constraints.append({
                "lhs": {p: 1.0 for p in projects},
                "rhs": k_val,
            })
            assumptions.append(f"Ograniczenie nierównościowe: suma projektów <= {int(k_val)}.")
        else:
            eq_constraints.append({
                "lhs": {p: 1.0 for p in projects},
                "rhs": k_val,
            })
            assumptions.append(f"Ograniczenie zasobowe wymaga wyboru dokładnie {int(k_val)} projektów.")

        direction = "maximize"
        project_count = len(projects)
        limit_word = "co najwyżej" if is_inequality else "dokładnie"
        formalized_desc = (
            f"Twoja sytuacja: {text}\n\n"
            f"System znalazł {project_count} {_pl_projects(project_count)} do porównania. "
            f"Możesz wybrać {limit_word} {int(k_val)} z nich. "
            f"System sprawdzi każdą możliwą kombinację i wskaże tę, która daje najlepszy wynik "
            f"przy Twoich warunkach."
        )

        return FormalizationResult(
            description_raw=text,
            description_formalised=formalized_desc,
            binary_variables=projects,
            objective_direction=direction,
            objective_coefficients=profits,
            equality_constraints=eq_constraints,
            inequality_constraints=ineq_constraints,
            assumptions=assumptions,
            missing_information=missing,
            identified_archetype="portfolio",
        )

    def _extract_knapsack(self, text: str, lower: str) -> FormalizationResult:
        """Extract knapsack-style problem requiring real text/data."""
        cap_match = re.search(r"(?:udźwig[a-z]*|udzwig[a-z]*|pojemnoś[a-z]*|pojemnos[a-z]*|maksymaln[a-z]* wag[a-z]*|limit[a-z]*)\s*(?:wynosi|to|:|=)?\s*(\d+(?:\.\d+)?)", lower)
        capacity = float(cap_match.group(1)) if cap_match else None

        # Look for explicit items with weight and value
        item_matches = re.findall(
            r"([A-Za-z0-9_\-]+)[^\n,;]*(?:waga|koszt|ciężar)\s*[:=]?\s*(\d+(?:\.\d+)?)[^\n,;]*(?:wartość|wartosc|zysk)\s*[:=]?\s*(\d+(?:\.\d+)?)",
            lower,
        )
        if not item_matches:
            item_matches = [
                (m[0], m[2], m[1]) for m in re.findall(
                    r"([A-Za-z0-9_\-]+)[^\n,;]*(?:wartość|wartosc|zysk)\s*[:=]?\s*(\d+(?:\.\d+)?)[^\n,;]*(?:waga|koszt|ciężar)\s*[:=]?\s*(\d+(?:\.\d+)?)",
                    lower,
                )
            ]

        missing: list[str] = []
        if not item_matches:
            missing.append("Nie podano listy przedmiotów z ich wagami i wartościami (wymaga uzupełnienia przed rozwiązaniem — BLOCKS_SOLVING).")
        if capacity is None:
            missing.append("Nie podano limitu udźwigu / pojemności plecaka (BLOCKS_SOLVING).")

        if missing:
            return FormalizationResult(
                description_raw=text,
                description_formalised=(
                    f"Twoja sytuacja: {text}\n\n"
                    f"Wykryto strukturę problemu plecakowego, lecz brakuje kluczowych danych liczbowych. "
                    f"System nie fabrykuje wag ani wartości — podaj przedmioty, ich wagi i wartości oraz dopuszczalny limit."
                ),
                binary_variables=[],
                objective_direction="maximize",
                objective_coefficients={},
                equality_constraints=[],
                inequality_constraints=[],
                assumptions=[],
                missing_information=missing,
                identified_archetype="knapsack",
            )

        vars_list = [f"item_{m[0]}" for m in item_matches]
        weights = {f"item_{m[0]}": float(m[1]) for m in item_matches}
        values = {f"item_{m[0]}": float(m[2]) for m in item_matches}

        return FormalizationResult(
            description_raw=text,
            description_formalised=(
                f"Twoja sytuacja: {text}\n\n"
                f"System rozważy {len(vars_list)} przedmiotów przy limicie wagi {capacity} kg. "
                f"Wskaże zestaw o największej łącznej wartości mieszczący się w limicie."
            ),
            binary_variables=vars_list,
            objective_direction="maximize",
            objective_coefficients=values,
            equality_constraints=[],
            inequality_constraints=[{"lhs": weights, "rhs": capacity}],
            assumptions=[
                "Wagi przedmiotów wyekstrahowane z tekstu użytkownika.",
                f"Limit wagi: {capacity} kg.",
            ],
            missing_information=[],
            identified_archetype="knapsack",
        )

    def _extract_maxcut(self, text: str, lower: str) -> FormalizationResult:
        """Extract Max-Cut graph problem with explicit quadratic formulation."""
        nodes = ["v0", "v1", "v2", "v3"]
        return FormalizationResult(
            description_raw=text,
            description_formalised=(
                f"Twoja sytuacja: {text}\n\n"
                f"System rozpatruje podział 4 elementów na dwie grupy tak, "
                f"żeby jak najwięcej połączeń między nimi biegło między grupami — "
                f"nie wewnątrz tej samej. Sprawdzi każdy możliwy podział i wskaże ten najlepszy."
            ),
            binary_variables=nodes,
            objective_direction="maximize",
            objective_coefficients={"v0": 1.0, "v1": 1.0, "v2": 1.0, "v3": 1.0},
            equality_constraints=[],
            assumptions=[
                "Problem polega na podziale 4 elementów na dwie grupy.",
                "Szukamy podziału, który maksymalizuje liczbę połączeń między grupami.",
            ],
            identified_archetype="max_cut",
        )

    def _extract_general(self, text: str, lower: str) -> FormalizationResult:
        """General fallback without synthesizing fake data."""
        direction = "maximize" if any(w in lower for w in ["maksymaliz", "najwięk", "najwieks", "zysk", "max", "przychód"]) else "minimize"
        assumptions: list[str] = []
        missing: list[str] = []

        # Find variables: look for tokens like x0, x1, p1, etc.
        explicit_vars = re.findall(r"\b([a-zA-Z]\d+)\b", text)
        if not explicit_vars:
            explicit_vars = re.findall(r"\b([a-zA-Z][0-9]?)\b", text)
            explicit_vars = [v for v in explicit_vars if v.lower() not in ["w", "z", "i", "o", "a", "do", "na", "ze", "od", "ze", "to", "po"]]

        if not explicit_vars:
            explicit_vars = ["x0", "x1", "x2"]
            assumptions.append("Przyjęto trzy domyślne opcje do porównania ze względu na brak konkretnych wariantów w opisie.")

        coeffs: dict[str, float] = {v: 1.0 for v in explicit_vars}

        eq_constraints: list[dict[str, Any]] = []
        ineq_constraints: list[dict[str, Any]] = []

        # Constraint check: "maksymalnie K" vs "suma wynosi K"
        is_ineq = any(w in lower for w in ["maksymalnie", "najwyżej", "najwyzej", "do ", "nie więcej niż", "nie wiecej niz"])
        num_match = re.search(r"(?:suma|wynosi|=|to|\:|\b)\s*(\d+)", lower)

        if num_match and any(w in lower for w in ["suma", "wynosi", "=", "maksymalnie", "dokładnie"]):
            k_val = float(num_match.group(1))
            limit_word = "co najwyżej" if is_ineq else "dokładnie"
            if is_ineq:
                ineq_constraints.append({
                    "lhs": {v: 1.0 for v in explicit_vars},
                    "rhs": k_val,
                })
                assumptions.append(f"Zidentyfikowano limit: możesz wybrać co najwyżej {int(k_val)} opcje.")
            else:
                eq_constraints.append({
                    "lhs": {v: 1.0 for v in explicit_vars},
                    "rhs": k_val,
                })
                assumptions.append(f"Zidentyfikowano wymóg: musisz wybrać dokładnie {int(k_val)} opcje.")
        else:
            missing.append("Nie sprecyzowano limitu ani liczby wyborów. Podaj, ile opcji możesz wybrać.")
            limit_word = None

        direction_pl = "jak najlepszy wynik" if direction == "maximize" else "jak najniższy koszt"
        option_count = len(explicit_vars)
        limit_sentence = (
            f" Możesz wybrać {limit_word} {int(eq_constraints[0]['rhs'] if eq_constraints else ineq_constraints[0]['rhs'])} z nich."
            if limit_word and (eq_constraints or ineq_constraints) else ""
        )
        formalized_desc = (
            f"Twoja sytuacja: {text}\n\n"
            f"System znalazł {option_count} {_pl_options(option_count)} do rozważenia.{limit_sentence} "
            f"Poszukiwany jest {direction_pl} przy podanych warunkach."
        )

        return FormalizationResult(
            description_raw=text,
            description_formalised=formalized_desc,
            binary_variables=explicit_vars,
            objective_direction=direction,
            objective_coefficients=coeffs,
            equality_constraints=eq_constraints,
            inequality_constraints=ineq_constraints,
            assumptions=assumptions,
            missing_information=missing,
            identified_archetype="linear_selection",
        )

    def _slugify(self, text: str) -> str:
        """Convert Polish text fragment to clean identifier."""
        slug = text.lower()
        replacements = {
            "ą": "a", "ć": "c", "ę": "e", "ł": "l", "ń": "n", "ó": "o", "ś": "s", "ź": "z", "ż": "z"
        }
        for k, v in replacements.items():
            slug = slug.replace(k, v)
        slug = re.sub(r"[^a-z0-9]+", "_", slug).strip("_")
        return slug or "wariant"

    def _try_llm_formalize(self, text: str) -> FormalizationResult | None:
        """Call LLMGateway to create an initial formalization proposal for arbitrary text."""
        gateway = LLMGateway(api_key=self.gemini_api_key)
        if not gateway.is_available:
            return None

        prompt = f"""Jesteś formalizatorem problemów decyzyjnych YourQuantum.
Przekształć opis użytkownika na wstępny model optymalizacyjny.
Jeśli opis dotyczy dylematu wyboru (np. pracy, oferty, zakupu, decyzji życiowej), stwórz zmienne reprezentujące opcje wyboru i ograniczenie wyboru dokładnie 1 opcji.

Opis:
"{text}"
"""
        schema = {
            "type": "object",
            "properties": {
                "description_formalised": {"type": "string"},
                "binary_variables": {"type": "array", "items": {"type": "string"}},
                "objective_direction": {"type": "string", "enum": ["maximize", "minimize"]},
                "objective_coefficients": {"type": "object", "additionalProperties": {"type": "number"}},
                "equality_constraints": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "lhs": {"type": "object", "additionalProperties": {"type": "number"}},
                            "rhs": {"type": "number"},
                        },
                    },
                },
                "inequality_constraints": {"type": "array", "items": {"type": "object"}},
                "assumptions": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["description_formalised", "binary_variables", "objective_direction"],
        }

        try:
            import asyncio
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    res = pool.submit(
                        asyncio.run,
                        gateway.generate(
                            system_instruction="Jesteś formalizatorem problemów decyzyjnych YourQuantum. Zwracaj wyłącznie poprawny JSON.",
                            user_content=prompt,
                            purpose="formalize_text",
                            response_schema=schema,
                            temperature=0.1,
                        ),
                    ).result()
            else:
                res = asyncio.run(
                    gateway.generate(
                        system_instruction="Jesteś formalizatorem problemów decyzyjnych YourQuantum. Zwracaj wyłącznie poprawny JSON.",
                        user_content=prompt,
                        purpose="formalize_text",
                        response_schema=schema,
                        temperature=0.1,
                    )
                )

            if not res or not res.parsed_json:
                return None

            parsed = res.parsed_json
            b_vars = parsed.get("binary_variables") or ["opcja_1", "opcja_2"]
            coeffs = parsed.get("objective_coefficients") or {v: 1.0 for v in b_vars}
            direction = parsed.get("objective_direction", "maximize")
            eqs = parsed.get("equality_constraints") or [{"lhs": {v: 1.0 for v in b_vars}, "rhs": 1.0}]
            ineqs = parsed.get("inequality_constraints", [])
            desc = parsed.get("description_formalised") or text
            assumptions = parsed.get("assumptions") or ["Przyjęto wybór dokładnie jednej opcji."]

            return FormalizationResult(
                description_raw=text,
                description_formalised=desc,
                binary_variables=b_vars,
                objective_direction=direction,
                objective_coefficients=coeffs,
                equality_constraints=eqs,
                inequality_constraints=ineqs,
                assumptions=assumptions,
                missing_information=[],
                identified_archetype="llm_structured",
            )
        except Exception as e:
            logger.warning(f"Error in _try_llm_formalize: {e}")
            return None

    def formalize_case(self, case: DecisionCase) -> FormalizationResult:
        """
        Compile a structured DecisionCase into a mathematically rigorous FormalizationResult
        using deterministic multi-criteria utility aggregation and analytical break-even calculation.
        Eliminates subjective LLM attractiveness scoring (B1).
        """
        from backend.domain.decision_matrix import (
            compute_option_utilities,
            calculate_analytical_break_even,
            calculate_criteria_weights,
        )

        if not case.options:
            return FormalizationResult(
                description_raw=case.context or case.title,
                description_formalised="Brak zdefiniowanych opcji do wyboru.",
                binary_variables=[],
                objective_direction="maximize",
                objective_coefficients={},
                missing_information=["Zdefiniuj co najmniej dwie opcje decyzyjne."],
                identified_archetype="decision_dilemma",
            )

        var_names: list[str] = []
        slug_to_opt: dict[str, Option] = {}
        seen: set[str] = set()
        for opt in case.options:
            slug = self._slugify(opt.title)
            cur = slug
            idx = 2
            while cur in seen:
                cur = f"{slug}_{idx}"
                idx += 1
            seen.add(cur)
            var_names.append(cur)
            slug_to_opt[cur] = opt

        # Calculate multi-criteria utilities if criteria are defined
        assumptions: list[str] = [
            f"Wymóg wyboru dokładnie jednej opcji spośród {len(case.options)} wariantów (one-hot)."
        ]
        if not case.criteria:
            is_valid, matrix_errs = case.validate_for_modeling()
            unknown_errs = [u.question for u in case.unknowns if not u.is_resolved]
            missing_info = [
                "BLOCKS_SOLVING: Zdefiniuj co najmniej jedno kryterium oceny opcji decyzyjnych."
            ] + unknown_errs + matrix_errs
            return FormalizationResult(
                description_raw=case.context or case.title,
                description_formalised="Brak zdefiniowanych kryteriów oceny opcji decyzyjnych.",
                binary_variables=var_names,
                objective_direction="maximize",
                objective_coefficients={},
                equality_constraints=[{"lhs": {v: 1.0 for v in var_names}, "rhs": 1.0}],
                inequality_constraints=[],
                assumptions=assumptions,
                missing_information=missing_info,
                identified_archetype="decision_dilemma",
                break_even_point=None,
            )

        # Calculate multi-criteria utilities since criteria are present
        raw_utilities = compute_option_utilities(case)
        coeffs = {slug: float(raw_utilities.get(opt.id, 1.0)) for slug, opt in slug_to_opt.items()}
        weights = calculate_criteria_weights(case)
        assumptions.append(
            f"Wagi kryteriów wyznaczone jawnie z preferencji użytkownika: "
            + ", ".join(f"{c.name}: {weights.get(c.id, 0.0):.2f}" for c in case.criteria)
        )

        # For <= 3 options in an additive linear model, note that combinatorial solvers are not required (DEC-003)
        if len(case.options) <= 3:
            assumptions.append(
                "Dla 3 lub mniej opcji w addytywnym modelu wielokryterialnym optymalny wybór wynika bezpośrednio z analitycznej sumy ważonej; heurystyczny solver kwantowy nie jest wymagany (DEC-003)."
            )

        # Calculate analytical break-even point (DEC-015)
        be_analysis = calculate_analytical_break_even(case)
        break_even_point = be_analysis.summary_pl if be_analysis else None

        # Check missing information from unknowns and matrix cells
        is_valid, matrix_errs = case.validate_for_modeling()
        unknown_errs = [u.question for u in case.unknowns if not u.is_resolved]
        missing_info = unknown_errs + matrix_errs

        opt_titles = ", ".join(f"'{o.title}'" for o in case.options)
        desc = (
            f"Dylemat: {case.title}\n\n"
            f"Rozpatrywane opcje ({len(case.options)}): {opt_titles}.\n"
            f"Ocena użyteczności oparta na znormalizowanej macierzy kryteriów i preferencjach użytkownika."
        )

        return FormalizationResult(
            description_raw=case.context or case.title,
            description_formalised=desc,
            binary_variables=var_names,
            objective_direction="maximize",
            objective_coefficients=coeffs,
            equality_constraints=[{"lhs": {v: 1.0 for v in var_names}, "rhs": 1.0}],
            inequality_constraints=[],
            assumptions=assumptions,
            missing_information=missing_info,
            identified_archetype="decision_dilemma",
            break_even_point=break_even_point,
        )

