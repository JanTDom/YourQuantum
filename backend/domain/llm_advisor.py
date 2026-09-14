"""
YourQuantum — LLM Advisor & Human Case Structurer
Supports Gemini API (GEMINI_API_KEY) and OpenAI (OPENAI_API_KEY) for
interpreting everyday human dilemmas into structured DecisionCase objects.
Strict rule: LLM assists in structuring human dilemmas and asking clarification
questions; it NEVER fabricates solver execution or mathematical proof.
When offline or without API keys, provides honest, zero-hallucination heuristic fallback.
"""
from __future__ import annotations

import json
import logging
import os
import re
import uuid
from typing import Any
from dotenv import load_dotenv

load_dotenv()

from backend.domain.decision_case import (
    Criterion,
    DecisionCase,
    Fact,
    InputQuality,
    Option,
    ScoredValue,
    Tradeoff,
    Unknown,
)
from backend.infrastructure.llm_gateway import LLMGateway

logger = logging.getLogger(__name__)


def _verify_quote_in_text(quote: str, text: str) -> bool:
    """Verifies that a quoted snippet exists within the source text using normalized comparison."""
    if not quote or not text:
        return False
    norm_quote = re.sub(r"\s+", " ", quote.strip().lower())
    norm_text = re.sub(r"\s+", " ", text.strip().lower())
    return norm_quote in norm_text


DECISION_STRUCTURE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "options": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["id", "title"],
            },
        },
        "criteria": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "direction": {"type": "string", "enum": ["maximize", "minimize"]},
                    "weight": {"type": "number"},
                    "unit": {"type": "string"},
                },
                "required": ["id", "name", "direction", "weight"],
            },
        },
        "values": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "option_id": {"type": "string"},
                    "criterion_id": {"type": "string"},
                    "value": {"type": "number"},
                    "unit": {"type": "string"},
                    "quote_from_user_text": {"type": "string"},
                },
                "required": ["option_id", "criterion_id", "value", "quote_from_user_text"],
            },
        },
        "unknowns": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "impact_description": {"type": "string"},
                    "default_assumption": {"type": "string"},
                },
                "required": ["question"],
            },
        },
        "tradeoffs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "gain": {"type": "string"},
                    "sacrifice": {"type": "string"},
                },
                "required": ["description"],
            },
        },
        "priority_tokens": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["options", "criteria", "values"],
}


async def extract_decision_structure(
    query: str,
    gateway: LLMGateway | None = None,
) -> dict[str, Any]:
    """
    N2: Extract decision criteria, options, and values with quote verification against user query.
    Values without a verified quote from user text are strictly rejected.
    Offline fallback: options from heuristic regex, criteria from priority tokens, values empty.
    """
    gw = gateway or LLMGateway()
    cleaned = query.strip()
    if not cleaned:
        return {"options": [], "criteria": [], "values": []}

    if gw.is_available:
        sys_inst = (
            "Jesteś precyzyjnym analitykiem decyzji YourQuantum. "
            "Twoim zadaniem jest wyodrębnienie z tekstu użytkownika: "
            "1. options: co najmniej 2 wariantów wyboru. "
            "2. criteria: 2-4 kluczowych kryteriów oceny (kierunek maximize/minimize, waga 0-1 sumująca się do 1.0). "
            "3. values: wartości liczbowych dla komórek [option_id, criterion_id]. "
            "BARDZO WAŻNE: Wartość możesz podać TYLKO wtedy, gdy użytkownik podał ją wprost w tekście. "
            "Pole 'quote_from_user_text' MUSI zawierać DOKŁADNY cytat fragmentu tekstu użytkownika, z którego pochodzi liczba. "
            "Jeśli danej liczby nie ma w tekście, NIE WOLNO JEJ ZMYŚLAĆ — nie twórz wtedy rekordu w values. "
            "4. unknowns: pytania o brakujące kluczowe dane. "
            "5. tradeoffs: kompromisy między wariantami."
        )
        resp = await gw.generate(
            system_instruction=sys_inst,
            user_content=f"Tekst dylematu użytkownika:\n\"\"\"{cleaned}\"\"\"",
            purpose="extract_decision_structure",
            response_schema=DECISION_STRUCTURE_SCHEMA,
            temperature=0.1,
        )
        if resp.parsed_json:
            parsed = resp.parsed_json
            options = parsed.get("options") or []
            criteria = parsed.get("criteria") or []
            raw_values = parsed.get("values") or []

            # Normalize criteria weights so sum equals 1.0
            if criteria:
                tot = sum(float(c.get("weight", 0.0)) for c in criteria)
                if tot > 0:
                    for c in criteria:
                        c["weight"] = round(float(c.get("weight", 0.0)) / tot, 3)
                else:
                    eq = round(1.0 / len(criteria), 3)
                    for c in criteria:
                        c["weight"] = eq

            verified_values = []
            for v in raw_values:
                quote = str(v.get("quote_from_user_text", "")).strip()
                if _verify_quote_in_text(quote, cleaned):
                    verified_values.append(v)
                else:
                    logger.info(
                        "Odrzucono nieuziemioną wartość dla %s/%s: brak cytatu '%s' w tekście użytkownika.",
                        v.get("option_id"),
                        v.get("criterion_id"),
                        quote,
                    )

            return {
                "title": parsed.get("title"),
                "options": options,
                "criteria": criteria,
                "values": verified_values,
                "unknowns": parsed.get("unknowns") or [],
                "tradeoffs": parsed.get("tradeoffs") or [],
                "priority_tokens": parsed.get("priority_tokens") or [],
            }

    # Offline deterministic fallback
    advisor = LLMAdvisor()
    case = advisor.heuristic_analyze(cleaned)
    criteria_dicts = [
        {"id": c.id, "name": c.name, "direction": c.direction, "weight": c.weight, "unit": c.unit}
        for c in case.criteria
    ]
    options_dicts = [
        {"id": o.id, "title": o.title, "description": o.description}
        for o in case.options
    ]
    return {
        "title": case.title,
        "options": options_dicts,
        "criteria": criteria_dicts,
        "values": [],  # Empty by design — no fabricated values
        "unknowns": [u.model_dump() for u in case.unknowns],
        "tradeoffs": [t.model_dump() for t in case.tradeoffs],
        "priority_tokens": case.priority_tokens,
    }


class LLMAdvisor:
    """Intelligent advisor for parsing everyday human dilemmas."""

    def __init__(
        self,
        gemini_api_key: str | None = None,
        openai_api_key: str | None = None,
    ):
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

    def analyze_case(self, user_text: str) -> DecisionCase:
        """Parse human text into structured DecisionCase."""
        cleaned = user_text.strip()
        if not cleaned:
            return DecisionCase(
                title="Pusty opis sytuacji",
                context="",
                status="intake",
                unknowns=[
                    Unknown(
                        question="O jakiej sytuacji lub decyzji chciałbyś porozmawiać?",
                        impact_description="Brak punktu wyjścia do analizy.",
                    )
                ],
            )

        # Try online LLM if keys are available
        if self.gemini_api_key:
            try:
                res = self._call_gemini(cleaned)
                if res is not None:
                    return res
            except Exception as e:
                logger.warning(f"Gemini API call failed: {e}; falling back to deterministic structurer.")

        if self.openai_api_key:
            try:
                res = self._call_openai(cleaned)
                if res is not None:
                    return res
            except Exception as e:
                logger.warning(f"OpenAI API call failed: {e}; falling back to deterministic structurer.")

        return self.heuristic_analyze(cleaned)

    def heuristic_analyze(self, text: str) -> DecisionCase:
        """
        Deterministic, zero-hallucination extraction of options, facts,
        and missing criteria from text.
        """
        lower = text.lower()
        title = self._generate_clean_title(text)

        facts: list[Fact] = []
        options: list[Option] = []
        criteria: list[Criterion] = []
        unknowns: list[Unknown] = []
        tradeoffs: list[Tradeoff] = []

        # 1. Detect dilemma or choices: "czy X, czy Y", "albo X albo Y", "X czy Y", "między X a Y"
        dilemma_match = re.search(r"czy\s+(.+?)(?:,|\s+)\s*czy\s+(.+)", text, re.IGNORECASE)
        if not dilemma_match:
            dilemma_match = re.search(r"(?:wybrać|wybieram|wybór|wybor)?\s*(?:między|miedzy)\s+(.+?)\s+a\s+(.+)", text, re.IGNORECASE)
        if not dilemma_match:
            dilemma_match = re.search(r"albo\s+(.+?)\s+albo\s+(.+)", text, re.IGNORECASE)

        if dilemma_match:
            opt_a_title = dilemma_match.group(1).strip(" .?!,").capitalize()
            opt_b_title = dilemma_match.group(2).strip(" .?!,").capitalize()

            opt_a = Option(
                id="opt_1",
                title=opt_a_title,
                description=f"Opcja A: {opt_a_title}",
            )
            opt_b = Option(
                id="opt_2",
                title=opt_b_title,
                description=f"Opcja B: {opt_b_title}",
            )
            options.extend([opt_a, opt_b])

            unknowns.append(
                Unknown(
                    question="Jakie czynniki są dla Ciebie najważniejsze przy tym wyborze (np. wynagrodzenie, spokój, stabilność, czas wolny)?",
                    impact_description="Pozwoli obiektywnie porównać obie opcje.",
                    default_assumption="Równowaga między stabilnością a rozwojem.",
                )
            )
            unknowns.append(
                Unknown(
                    question=f"Co najbardziej zyskujesz wybierając '{opt_a_title}', a co ryzykujesz?",
                    impact_description="Pozwoli zmapować kompromisy i ukryte koszty.",
                )
            )
            tradeoffs.append(
                Tradeoff(
                    option_a_id="opt_1",
                    option_b_id="opt_2",
                    description=f"Wybór między '{opt_a_title}' a '{opt_b_title}'",
                    gain=f"to co daje {opt_a_title}",
                    sacrifice=f"to co daje {opt_b_title}",
                )
            )
        elif any(w in lower for w in ["dwóch", "dwoch", "dwie", "dwa", "dwoje", "ofert", "wybór", "wybor", "wybrać", "wybrac", "wahać", "waham"]):
            # For phrases like "z dwóch wydawnictw", "dwie propozycje", "dwie oferty"
            opt_a_title = "Pierwsza oferta"
            opt_b_title = "Druga oferta"
            if "wydaw" in lower:
                opt_a_title = "Pierwsze wydawnictwo"
                opt_b_title = "Drugie wydawnictwo"
            elif "prac" in lower:
                opt_a_title = "Pierwsza oferta pracy"
                opt_b_title = "Druga oferta pracy"
            elif "firm" in lower:
                opt_a_title = "Pierwsza firma"
                opt_b_title = "Druga firma"

            opt_a = Option(
                id="opt_1",
                title=opt_a_title,
                description=f"Wybór: {opt_a_title}",
            )
            opt_b = Option(
                id="opt_2",
                title=opt_b_title,
                description=f"Wybór: {opt_b_title}",
            )
            options.extend([opt_a, opt_b])

            unknowns.append(
                Unknown(
                    question="Jakie konkretne warunki (np. wynagrodzenie, forma współpracy, zakres obowiązków) oferuje każde z nich?",
                    impact_description="Niezbędne, aby matematycznie i obiektywnie porównać obie opcje.",
                    default_assumption="Warunki obu ofert są zbliżone.",
                )
            )
            unknowns.append(
                Unknown(
                    question="Co jest dla Ciebie najważniejszym kryterium sukcesu przy tym wyborze (np. zarobki, kultura firmy, rozwój, swoboda)?",
                    impact_description="Pozwoli nadać wagę poszczególnym czynnikom decyzyjnym.",
                    default_assumption="Równowaga między stabilnością a satysfakcją z pracy.",
                )
            )
            tradeoffs.append(
                Tradeoff(
                    option_a_id="opt_1",
                    option_b_id="opt_2",
                    description=f"Wybór między '{opt_a_title}' a '{opt_b_title}'",
                    gain=f"zalety opcji {opt_a_title}",
                    sacrifice=f"zalety opcji {opt_b_title}",
                )
            )
        else:
            # Check for multiple options named explicitly (e.g. A, B, C or 5 projektów)
            items_match = re.findall(r"(?:projekt|wariant|opcja|kandydat)\s+([A-Za-z0-9_]+)", text, re.IGNORECASE)
            if items_match:
                for idx, it in enumerate(items_match):
                    options.append(
                        Option(
                            id=f"opt_{it.lower()}",
                            title=f"Projekt {it.upper()}",
                            description=f"Rozważana opcja {it.upper()}",
                        )
                    )
            else:
                # Check for "N projektów" / "N inwestycji"
                n_match = re.search(r"(\d+)\s+(?:projektów|projektow|inwestycji|zadań|zadan|opcji)", lower)
                if n_match:
                    count = min(int(n_match.group(1)), 10)
                    for i in range(1, count + 1):
                        options.append(
                            Option(
                                id=f"opt_{i}",
                                title=f"Projekt {i}",
                                description=f"Projekt inwestycyjny #{i}",
                            )
                        )
                    unknowns.append(
                        Unknown(
                            question="Jaki jest przewidywany zysk lub koszt dla każdego z tych projektów?",
                            impact_description="Niezbędne do wyznaczenia najlepszej kombinacji.",
                        )
                    )

        # 2. Extract numbers as candidate facts (budgets, counts)
        k_match = re.search(r"(?:wybrać|wybierz|wybór)\s+(\d+)", lower)
        if k_match:
            facts.append(
                Fact(
                    label="Docelowa liczba wyborów",
                    value=int(k_match.group(1)),
                    unit="szt.",
                    source_text=k_match.group(0),
                )
            )

        budget_match = re.search(r"(?:budżet|koszt|maksymalnie|limit)\s*(?:wynosi|to|:)?\s*(\d+(?:[.,]\d+)?)", lower)
        if budget_match:
            val = float(budget_match.group(1).replace(",", "."))
            facts.append(
                Fact(
                    label="Limit budżetu lub zasobów",
                    value=val,
                    source_text=budget_match.group(0),
                )
            )

        # 3. Assess input quality & degrees of freedom
        quality = self._assess_input_quality(text, options_count=len(options))

        status = "clarification" if (unknowns or quality.level != "sufficient") else "ready_for_modeling"

        if re.search(r"\b(prac\w*|zarobk\w*|etat\w*|karier\w*|pensj\w*|zatrudnieni\w*|b2b|pracodawc\w*|korporacj\w*|startup\w*)\b", lower):
            priority_tokens = [
                "💰 Wyższe zarobki i finanse",
                "🌿 Spokój i kultura pracy",
                "🚀 Autonomia decyzyjna",
                "🛡️ Stabilność zatrudnienia",
            ]
            criteria = [
                Criterion(id="crit_zarobki", name="Wynagrodzenie i finanse", direction="maximize", weight=0.25, unit="PLN"),
                Criterion(id="crit_kultura", name="Spokój i kultura pracy", direction="maximize", weight=0.25, unit="skala 1-10"),
                Criterion(id="crit_autonomia", name="Autonomia decyzyjna", direction="maximize", weight=0.25, unit="skala 1-10"),
                Criterion(id="crit_stabilnosc", name="Stabilność zatrudnienia", direction="maximize", weight=0.25, unit="skala 1-10"),
            ]
        elif re.search(r"\b(mieszkan\w*|lokal\w*|biur\w*|samochód\w*|samochod\w*|nieruchomoś\w*|działk\w*|kupić|zakup)\b", lower):
            priority_tokens = [
                "💰 Niższa cena i koszty",
                "📍 Dogodna lokalizacja",
                "🌟 Wysoki standard i jakość",
                "🛡️ Bezpieczeństwo i trwałość",
            ]
            criteria = [
                Criterion(id="crit_cena", name="Cena i koszty zakupu", direction="minimize", weight=0.3, unit="PLN"),
                Criterion(id="crit_jakosc", name="Jakość i standard wykonania", direction="maximize", weight=0.25, unit="skala 1-10"),
                Criterion(id="crit_lokalizacja", name="Lokalizacja i dostępność", direction="maximize", weight=0.25, unit="skala 1-10"),
                Criterion(id="crit_eksploatacja", name="Koszty eksploatacji", direction="minimize", weight=0.2, unit="PLN/mies."),
            ]
        elif re.search(r"\b(inwestycj\w*|projekt\w*|budżet\w*|portfel\w*|zysk\w*|stopa\s+zwrotu)\b", lower):
            priority_tokens = [
                "📈 Maksymalny zwrot z inwestycji",
                "🛡️ Ograniczenie ryzyka",
                "⏱️ Krótki czas realizacji",
                "💵 Optymalizacja budżetu",
            ]
            criteria = [
                Criterion(id="crit_zwrot", name="Oczekiwany zwrot / zysk", direction="maximize", weight=0.35, unit="PLN / %"),
                Criterion(id="crit_ryzyko", name="Poziom ryzyka", direction="minimize", weight=0.25, unit="skala 1-10"),
                Criterion(id="crit_budzet", name="Nakłady finansowe / budżet", direction="minimize", weight=0.25, unit="PLN"),
                Criterion(id="crit_czas", name="Czas zwrotu / horyzont", direction="minimize", weight=0.15, unit="miesiące"),
            ]
        else:
            priority_tokens = [
                "🎯 Maksymalna skuteczność",
                "💰 Ograniczenie kosztów",
                "🛡️ Minimalizacja ryzyka",
                "⏱️ Szybkość i wygoda",
            ]
            criteria = [
                Criterion(id="crit_skutecznosc", name="Skuteczność i korzyści", direction="maximize", weight=0.35, unit="skala 1-10"),
                Criterion(id="crit_koszt", name="Koszty i nakład zasobów", direction="minimize", weight=0.25, unit="PLN / pkt"),
                Criterion(id="crit_ryzyko", name="Ryzyko niepowodzenia", direction="minimize", weight=0.25, unit="skala 1-10"),
                Criterion(id="crit_wygoda", name="Wygoda i czas wdrożenia", direction="maximize", weight=0.15, unit="skala 1-10"),
            ]

        return DecisionCase(
            title=title,
            context=text,
            status=status,
            facts=facts,
            options=options,
            criteria=criteria,
            unknowns=unknowns,
            tradeoffs=tradeoffs,
            priority_tokens=priority_tokens,
            input_quality=quality,
        )

    def _assess_input_quality(self, text: str, options_count: int = 0) -> InputQuality:
        """
        Evaluate whether the user prompt contains enough degrees of freedom
        and specific data to model an exact mathematical dilemma.
        Delegates to cognitive domain quality gate.
        """
        from backend.domain.cognitive.quality_gate import assess_input_quality
        return assess_input_quality(text, options_count=options_count)

    def _generate_clean_title(self, text: str) -> str:
        """Create concise headline in sentence case."""
        t = text.strip()
        if len(t) > 60:
            t = t[:57] + "..."
        if t:
            return t[0].upper() + t[1:]
        return "Nowa decyzja"

    def _build_case_from_structure(self, struct: dict[str, Any], text: str) -> DecisionCase:
        options = [
            Option(
                id=o.get("id", f"opt_{i+1}"),
                title=o.get("title", f"Opcja {i+1}"),
                description=o.get("description", ""),
            )
            for i, o in enumerate(struct.get("options", []))
        ]
        criteria = [
            Criterion(
                id=c.get("id", f"crit_{i+1}"),
                name=c.get("name", f"Kryterium {i+1}"),
                direction=c.get("direction", "maximize"),
                weight=float(c.get("weight", 1.0 / max(len(struct.get("criteria", [])), 1))),
                unit=c.get("unit"),
            )
            for i, c in enumerate(struct.get("criteria", []))
        ]
        unknowns = [
            Unknown(
                id=f"unk_{uuid.uuid4().hex[:8]}",
                question=u.get("question", ""),
                impact_description=u.get("impact_description", ""),
                default_assumption=u.get("default_assumption"),
            )
            for u in struct.get("unknowns", [])
            if u.get("question")
        ]
        tradeoffs = [
            Tradeoff(
                description=t.get("description", ""),
                gain=t.get("gain", ""),
                sacrifice=t.get("sacrifice", ""),
            )
            for t in struct.get("tradeoffs", [])
            if t.get("description")
        ]
        priority_tokens = struct.get("priority_tokens") or [
            "💰 Niższy koszt / Finanse",
            "🌿 Spokój i komfort psychiczny",
            "🛡️ Bezpieczeństwo i stabilność",
            "🚀 Rozwój i perspektywy",
        ]
        score_matrix: dict[str, dict[str, ScoredValue]] = {}
        for v in struct.get("values", []):
            opt_id = v.get("option_id")
            crit_id = v.get("criterion_id")
            val = v.get("value")
            if opt_id and crit_id and val is not None:
                score_matrix.setdefault(opt_id, {})[crit_id] = ScoredValue(
                    value=float(val),
                    unit=v.get("unit"),
                    provenance="user_supplied",
                    source_ref="user_input",
                    confidence=1.0,
                )

        title = struct.get("title") or self._generate_clean_title(text)
        quality = self._assess_input_quality(text, options_count=len(options))
        status = "clarification" if (unknowns or quality.level != "sufficient") else "ready_for_modeling"

        return DecisionCase(
            title=title,
            context=text,
            status=status,
            options=options,
            criteria=criteria,
            unknowns=unknowns,
            tradeoffs=tradeoffs,
            priority_tokens=priority_tokens,
            score_matrix=score_matrix,
            input_quality=quality,
        )

    async def _call_gemini_async(self, text: str) -> DecisionCase | None:
        """Asynchronous call to LLMGateway to structure decision case."""
        gw = LLMGateway(api_key=self.gemini_api_key)
        struct = await extract_decision_structure(text, gateway=gw)
        if not struct.get("options") or not struct.get("criteria"):
            return None
        return self._build_case_from_structure(struct, text)

    def _call_gemini(self, text: str) -> DecisionCase | None:
        """Synchronous wrapper for extract_decision_structure."""
        try:
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    return None  # Avoid blocking current loop; caller should use analyze_case_async
            except RuntimeError:
                pass
            return asyncio.run(self._call_gemini_async(text))
        except Exception as e:
            logger.warning("Failed to analyze case synchronously with Gemini: %s", e)
            return None

    async def analyze_case_async(self, user_text: str) -> DecisionCase:
        """Asynchronous parsing of human dilemma without blocking event loop."""
        cleaned = user_text.strip()
        if not cleaned:
            return self.analyze_case(user_text)

        if self.gemini_api_key:
            try:
                res = await self._call_gemini_async(cleaned)
                if res is not None:
                    return res
            except Exception as e:
                logger.warning("Gemini async call failed: %s; falling back to heuristic.", e)

        return self.heuristic_analyze(cleaned)
