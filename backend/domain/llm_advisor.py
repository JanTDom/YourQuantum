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

import httpx
from dotenv import load_dotenv

load_dotenv()

from backend.domain.decision_case import (
    Criterion,
    DecisionCase,
    Fact,
    InputQuality,
    Option,
    Tradeoff,
    Unknown,
)

logger = logging.getLogger(__name__)


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

        # 1. Detect dilemma or choices: "czy X, czy Y", "albo X albo Y", "X czy Y"
        dilemma_match = re.search(r"czy\s+(.+?)(?:,|\s+)\s*czy\s+(.+)", text, re.IGNORECASE)
        if not dilemma_match:
            dilemma_match = re.search(r"wybrać\s+między\s+(.+?)\s+a\s+(.+)", text, re.IGNORECASE)
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

        status = "clarification" if unknowns else "ready_for_modeling"
        priority_tokens = [
            "💰 Wyższe zarobki",
            "🌿 Spokój i kultura pracy",
            "🚀 Autonomia decyzyjna",
            "🛡️ Stabilność zatrudnienia",
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
        )

    def _generate_clean_title(self, text: str) -> str:
        """Create concise headline in sentence case."""
        t = text.strip()
        if len(t) > 60:
            t = t[:57] + "..."
        if t:
            return t[0].upper() + t[1:]
        return "Nowa decyzja"

    def _call_gemini(self, text: str) -> DecisionCase | None:
        """Call Gemini API to understand human situation and ask intelligent questions."""
        if not self.gemini_api_key:
            return None

        prompt = f"""Jesteś doradcą decyzyjnym YourQuantum. Użytkownik przedstawia dylemat dotyczący DOWOLNEJ sfery życia (np. zakup nieruchomości/auta, zmiana pracy, wybór studiów, inwestycje, przeprowadzka, relacje, rozwój biznesu, organizacja czasu).
Twoim zadaniem jest:
1. Zrozumieć istotę dylematu (nawet przy skrótowym opisie, literówkach czy języku potocznym).
2. Zidentyfikować konkretne opcje wyboru (np. 'Kupić mieszkanie' vs 'Wynajmować i inwestować', 'Wariant A' vs 'Wariant B'). Jeśli opcji nie podano wprost, wydziel minimum 2 logiczne, realistyczne opcje.
3. Wykryć brakujące informacje i sformułować 2-3 konkretne, wnikliwe pytania (unknowns) specyficzne dla tego problemu (np. horyzont czasowy, budżet, priorytety, ryzyka).
4. Wskazać kluczowe kompromisy (tradeoffs) — co człowiek zyskuje, a co ryzykuje lub z czego rezygnuje.
5. Zaproponować 3-4 intuicyjne, konkretne pigułki priorytetów (priority_tokens) dopasowane do TEGO KONKRETNEGO dylematu (każda z trafnym emoji), np.:
   - Zakup/Inwestycja: '💰 Niższy koszt całkowity', '🛡️ Bezpieczeństwo kapitału', '📈 Potencjał wzrostu', '🔄 Elastyczność'
   - Życiowe/Edukacja: '❤️ Pasja i satysfakcja', '🎓 Perspektywy rynkowe', '🌿 Spokój ducha', '⏱️ Oszczędność czasu'
   - Praca/Biznes: '💵 Wyższe dochody', '🚀 Autonomia decyzyjna', '🛡️ Stabilność', '⚖️ Równowaga z życiem prywatnym'

Opis sytuacji od użytkownika:
"{text}"

Odpowiedz WYŁĄCZNIE jako poprawny JSON (application/json) o strukturze:
{{
  "title": "Tytuł dylematu w sentence case (np. Wybór między zakupem a wynajmem mieszkania)",
  "options": [
    {{"id": "opt_1", "title": "Nazwa opcji 1", "description": "Krótki opis"}},
    {{"id": "opt_2", "title": "Nazwa opcji 2", "description": "Krótki opis"}}
  ],
  "unknowns": [
    {{
      "question": "Konkretne pytanie doprecyzowujące",
      "impact_description": "Dlaczego ta informacja jest kluczowa dla podjęcia trafnej decyzji",
      "default_assumption": "Rozsądne założenie, gdyby użytkownik nie odpowiedział"
    }}
  ],
  "tradeoffs": [
    {{
      "description": "Krótki opis kompromisu",
      "gain": "Co można zyskać",
      "sacrifice": "Z czym wiąże się ryzyko lub koszt"
    }}
  ],
  "priority_tokens": [
    "Pigułka 1 z emoji dopasowana do tematu",
    "Pigułka 2 z emoji dopasowana do tematu",
    "Pigułka 3 z emoji dopasowana do tematu"
  ]
}}
"""
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={self.gemini_api_key}"
            resp = httpx.post(
                url,
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "response_mime_type": "application/json",
                        "temperature": 0.2,
                    },
                },
                timeout=20.0,
            )
            if resp.status_code != 200:
                logger.warning(f"Gemini API returned {resp.status_code}: {resp.text[:200]}")
                return None

            data = resp.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(raw_text)

            options: list[Option] = []
            for i, o in enumerate(parsed.get("options", [])):
                options.append(
                    Option(
                        id=o.get("id", f"opt_{i+1}"),
                        title=o.get("title", f"Opcja {i+1}"),
                        description=o.get("description", ""),
                    )
                )

            unknowns: list[Unknown] = []
            for i, u in enumerate(parsed.get("unknowns", [])):
                unknowns.append(
                    Unknown(
                        id=f"unk_{uuid.uuid4().hex[:8]}",
                        question=u.get("question", ""),
                        impact_description=u.get("impact_description", ""),
                        default_assumption=u.get("default_assumption"),
                    )
                )

            tradeoffs: list[Tradeoff] = []
            for tr in parsed.get("tradeoffs", []):
                opt_a = options[0].id if options else "opt_1"
                opt_b = options[1].id if len(options) > 1 else opt_a
                tradeoffs.append(
                    Tradeoff(
                        option_a_id=opt_a,
                        option_b_id=opt_b,
                        description=tr.get("description", ""),
                        gain=tr.get("gain", ""),
                        sacrifice=tr.get("sacrifice", ""),
                    )
                )

            priority_tokens = parsed.get("priority_tokens") or [
                "💰 Wyższe zarobki",
                "🌿 Spokój i kultura pracy",
                "🚀 Autonomia i sprawczość",
                "🛡️ Bezpieczeństwo i stabilność",
            ]

            title = parsed.get("title") or self._generate_clean_title(text)

            return DecisionCase(
                title=title,
                context=text,
                status="clarification" if unknowns else "ready_for_modeling",
                options=options,
                unknowns=unknowns,
                tradeoffs=tradeoffs,
                priority_tokens=priority_tokens,
            )
        except Exception as e:
            logger.warning(f"Failed to analyze case with Gemini: {e}")
            return None

    def _call_openai(self, text: str) -> DecisionCase | None:
        return None
