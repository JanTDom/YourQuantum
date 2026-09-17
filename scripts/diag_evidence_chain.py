#!/usr/bin/env python3
"""
scripts/diag_evidence_chain.py — Diagnostic tool for the YourQuantum evidence pipeline.
Performs web search -> document fetch -> evidence extraction -> quote verification
and outputs detailed diagnostic diagnostics without relaxing any verification checks.
"""
from __future__ import annotations

import asyncio
import difflib
import logging
import os
import sys
import unicodedata
from dotenv import load_dotenv

# Ensure repo root is in python path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

load_dotenv(os.path.join(repo_root, ".env"))
load_dotenv(os.path.join(repo_root, ".env.local"))

from backend.infrastructure.web_research.search_adapter import WebResearchAdapter
from backend.infrastructure.web_research.fetcher import SafeWebFetcher
from backend.infrastructure.web_research.extractor import EvidenceExtractor


def normalize_typography(text: str) -> str:
    """Normalize typography (quotes, dashes, non-breaking spaces) identically for both sides."""
    if not text:
        return ""
    # NFC normalization
    t = unicodedata.normalize("NFC", text)
    # Replace non-breaking spaces, zero-width spaces, soft hyphens
    t = t.replace("\u00a0", " ").replace("\u202f", " ").replace("\ufeff", "").replace("\u00ad", "")
    # Typographic quotes -> straight quotes
    t = t.replace("„", '"').replace("”", '"').replace("“", '"').replace("«", '"').replace("»", '"')
    t = t.replace("’", "'").replace("‘", "'").replace("`", "'")
    # Dashes -> hyphen-minus
    t = t.replace("–", "-").replace("—", "-").replace("−", "-")
    # Collapse whitespace
    return " ".join(t.split())


def longest_common_substring(s1: str, s2: str) -> str:
    """Find longest common substring purely for diagnostic reporting (never as acceptance criterion)."""
    matcher = difflib.SequenceMatcher(None, s1, s2)
    match = matcher.find_longest_match(0, len(s1), 0, len(s2))
    return s1[match.a : match.a + match.size] if match.size > 0 else ""


async def diagnose_query(query: str, max_results: int = 3) -> None:
    print("\n" + "=" * 80)
    print(f"DIAGNOZA ZAPYTANIA: {query}")
    print("=" * 80)

    adapter = WebResearchAdapter(provider="gemini")
    print(f"Status adaptera wyszukiwania: {adapter.get_status()}")

    print("\n--- KROK 1: WYSZUKIWANIE (Gemini Search Grounding) ---")
    search_results = await adapter.search(f"{query} analiza prawdopodobieństwo raport", max_results=max_results)
    print(f"Zwrócono adresów URL: {len(search_results)}")

    if not search_results:
        print("Brak wyników wyszukiwania. Koniec łańcucha.")
        return

    fetcher = SafeWebFetcher(timeout=10.0)
    extractor = EvidenceExtractor()

    for idx, sr in enumerate(search_results, 1):
        print(f"\n[DOKUMENT {idx}/{len(search_results)}]")
        print(f"  Otrzymany URL: {sr.url}")
        print(f"  Tytuł (wyszukiwarka): {sr.title}")
        print(f"  Zajawka: {sr.snippet[:120]}...")

        # KROK 2: POBIERANIE
        print("\n  --- KROK 2: POBIERANIE PRZEZ SafeWebFetcher ---")
        try:
            doc = await fetcher.fetch(sr.url)
        except Exception as e:
            print(f"  BŁĄD POBIERANIA: {e}")
            continue

        if not doc:
            print("  WYNIK POBIERANIA: None (np. zablokowany SSRF, timeout lub błąd HTTP).")
            continue

        page_len = len(doc.page_text) if doc.page_text else 0
        first_200 = doc.page_text[:200].replace("\n", " ") if doc.page_text else ""
        print(f"  Adres końcowy: {doc.url}")
        print(f"  Status HTTP: {doc.status_code}")
        print(f"  MIME / kodowanie: {doc.mime_type}")
        print(f"  Długość page_text: {page_len} znaków")
        print(f"  Pierwsze 200 znaków page_text: {repr(first_200)}")

        if page_len == 0:
            print("  Dokument pusty (brak tekstu po usunięciu HTML). Ekstrakcja niemożliwa.")
            continue

        # KROK 3: EKSTRAKCJA PRZEZ EvidenceExtractor
        print("\n  --- KROK 3: EKSTRAKCJA DOWODU ---")
        # Wywołujemy bezpieczny tekst tak jak w extractorze
        safe_text = doc.page_text[:20000]
        safe_text = safe_text.replace("<<<END_UNTRUSTED_WEB_CONTENT>>>", "[ESCAPED_BOUNDARY]")
        safe_text = safe_text.replace("<<<UNTRUSTED_WEB_CONTENT>>>", "[ESCAPED_BOUNDARY]")

        extracted_raw = None
        if extractor.gateway.is_available:
            try:
                extracted_raw = await extractor._extract_via_llm(
                    text=safe_text,
                    target_param=query[:80],
                    expected_unit="any",
                    description=f"Kluczowy fakt lub wskaźnik dla analizy: {query}",
                )
            except Exception as e:
                print(f"  Błąd wywołania bramki LLM w ekstraktorze: {e}")

        print(f"  Surowa odpowiedź ekstraktora (JSON): {extracted_raw}")

        if not extracted_raw or not extracted_raw.get("quote"):
            print("  Ekstraktor nie zwrócił dowodu lub pole 'quote' jest puste.")
            continue

        quote = str(extracted_raw.get("quote", "")).strip()
        print(f"  Twierdzenie (claim): {extracted_raw.get('claim')}")
        print(f"  Wartość (value): {extracted_raw.get('value')} {extracted_raw.get('unit')}")
        print(f"  Zwrócony cytat ({len(quote)} zn.): {repr(quote)}")

        # KROK 4: WERYFIKACJA CYTATU
        print("\n  --- KROK 4: WERYFIKACJA CYTATU W TEKŚCIE STRONY ---")
        exact_in_raw = quote in doc.page_text
        ws_norm_quote = " ".join(quote.split())
        ws_norm_text = " ".join(doc.page_text.split())
        ws_in_text = ws_norm_quote in ws_norm_text

        print(f"  Dosłowne dopasowanie (raw quote in raw text): {exact_in_raw}")
        print(f"  Dopasowanie ze zredukowanymi spacjami (ws-normalized): {ws_in_text}")

        # Normalizacja typograficzna
        typo_quote = normalize_typography(quote)
        typo_text = normalize_typography(doc.page_text)
        typo_in_text = typo_quote in typo_text
        print(f"  Dopasowanie po równoważnej normalizacji typografii: {typo_in_text}")

        if exact_in_raw or ws_in_text:
            print("  >>> STATUS: PASS (Weryfikacja zaliczona standardowo)")
        elif typo_in_text:
            print("  >>> STATUS: PASS PO NORMALIZACJI TYPOGRAFICZNEJ (cudzysłowy/myślniki/twarde spacje)")
        else:
            print("  >>> STATUS: FAIL (Cytat NIE znaleziony w tekście)")
            # Diagnostyka difflib: najdłuższy wspólny fragment
            lcs = longest_common_substring(typo_quote, typo_text)
            print(f"  Najdłuższy wspólny fragment ({len(lcs)} zn.): {repr(lcs)}")
            if len(lcs) > 0 and len(typo_quote) > 0:
                coverage = len(lcs) / len(typo_quote) * 100
                print(f"  Pokrycie cytatu przez najdłuższy wspólny fragment: {coverage:.1f}%")


async def main() -> None:
    queries = [
        "Czy Rosja zaatakuje kraje bałtyckie do końca 2027 roku?",
        "Czy Polska wybuduje pierwszą elektrownię jądrową do 2033 roku?",
        "Czy inflacja w Polsce spadnie poniżej celu NBP do końca 2026 roku?",
    ]
    if len(sys.argv) > 1:
        queries = [" ".join(sys.argv[1:])]

    for q in queries:
        await diagnose_query(q)


if __name__ == "__main__":
    asyncio.run(main())
