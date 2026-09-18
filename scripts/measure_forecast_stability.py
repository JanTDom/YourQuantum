#!/usr/bin/env python3
"""
scripts/measure_forecast_stability.py — Measures stability and reproducibility of forecast results.
Runs 5 consecutive runs of ActiveInferenceOrchestrator on the target query:
"Czy Rosja do końca tego roku napadnie na Polskę?"
Outputs a Markdown table with raw results.
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
from unittest.mock import AsyncMock
from dotenv import load_dotenv

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

load_dotenv(os.path.join(repo_root, ".env"))
load_dotenv(os.path.join(repo_root, ".env.local"))

from backend.domain.cognitive.active_inference_engine import ActiveInferenceOrchestrator
from backend.domain.cognitive.workspace import GlobalWorkspace
from backend.infrastructure.gemini_cognitive_adapter import GeminiCognitiveAdapter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("stability_test")


async def run_single(engine: ActiveInferenceOrchestrator, run_id: str, query: str) -> dict:
    os.environ["SEARCH_PROVIDER"] = "gemini"
    mock_session = AsyncMock()
    ws = GlobalWorkspace(goal=query, session_id=f"stability_{run_id}")
    res, updated_ws = await engine.run_intake(session=mock_session, query=query, workspace=ws)
    
    forecast_data = res.scenario_forecast or {}
    scenarios = forecast_data.get("scenarios", [])
    premises = forecast_data.get("evidence_premises", [])
    telemetry = forecast_data.get("telemetry", {})
    
    # Format distribution: sc1_prob / sc2_prob / ...
    probs = [f"{float(sc.get('probability', 0.0)) * 100:.1f}%".replace(".", ",") for sc in scenarios]
    dist_str = " / ".join(probs) if probs else "N/A"
    
    active_premises = [p for p in premises if p.get("is_accepted", False)]
    
    return {
        "run": run_id,
        "quotes_verified": telemetry.get("web_quotes_verified", 0),
        "active_premises": len(active_premises),
        "total_premises": len(premises),
        "impacts_proposed": telemetry.get("impacts_proposed", 0),
        "impacts_accepted": telemetry.get("impacts_accepted", 0),
        "impact_rejected_unsupported": telemetry.get("impact_rejected_unsupported", 0),
        "impact_documented_share": telemetry.get("impact_documented_share", 0.0),
        "distribution": dist_str,
        "dominant_scenario": forecast_data.get("dominant_scenario_id", ""),
        "dominant_prob": telemetry.get("dominant_probability", 0),
        "wall_time": telemetry.get("intake_wall_time_seconds", 0.0),
        "time_search": telemetry.get("time_search_seconds", 0.0),
        "time_fetch": telemetry.get("time_fetch_seconds", 0.0),
        "time_extraction": telemetry.get("time_extraction_seconds", 0.0),
        "time_decomposition": telemetry.get("time_decomposition_seconds", 0.0),
        "time_aggregation": telemetry.get("time_aggregation_seconds", 0.0),
    }


async def main():
    query = "Czy Rosja do końca tego roku napadnie na Polskę?"
    print(f"Rozpoczynam pomiar stabilności (10 biegów) dla zapytania: {query}")
    
    adapter = GeminiCognitiveAdapter()
    engine = ActiveInferenceOrchestrator(reasoning_port=adapter)
    results = []
    
    for i in range(1, 11):
        run_name = f"Bieg {chr(64 + i)}"  # A, B, C, D, E, F, G, H, I, J
        print(f"\n>>> Wykonuję {run_name}...")
        try:
            r = await run_single(engine, run_name, query)
            results.append(r)
            print(f"    Wynik: cytaty={r['quotes_verified']}, aktywne={r['active_premises']}, proposed={r['impacts_proposed']}, accepted={r['impacts_accepted']}, doc_share={r['impact_documented_share']}%, czas={r['wall_time']}s, rozkład={r['distribution']}")
        except Exception as e:
            logger.error("Błąd w %s: %s", run_name, e, exc_info=True)
            results.append({
                "run": run_name,
                "quotes_verified": 0,
                "active_premises": 0,
                "total_premises": 0,
                "impacts_proposed": 0,
                "impacts_accepted": 0,
                "impact_rejected_unsupported": 0,
                "impact_documented_share": 0.0,
                "distribution": f"BŁĄD: {e}",
                "dominant_prob": 0,
                "wall_time": 0.0,
                "time_search": 0.0,
                "time_fetch": 0.0,
                "time_extraction": 0.0,
                "time_decomposition": 0.0,
                "time_aggregation": 0.0,
            })

    print("\n" + "=" * 110)
    print("TABELA WYNIKÓW POMIARU STABILNOŚCI (10 BIEGÓW):")
    print("=" * 110)
    print("| Bieg | Zweryfikowane cytaty | Aktywne przesłanki | impacts_proposed | impacts_accepted | impact_rejected_unsupported | impact_documented_share | Czas całkowity | Rozkład |")
    print("|------|----------------------|--------------------|------------------|------------------|-----------------------------|-------------------------|----------------|---------|")
    for r in results:
        doc_share_str = f"{r['impact_documented_share']:.1f}%".replace(".", ",")
        wall_str = f"{r['wall_time']:.2f} s".replace(".", ",")
        print(f"| {r['run']} | {r['quotes_verified']} | {r['active_premises']} | {r['impacts_proposed']} | {r['impacts_accepted']} | {r['impact_rejected_unsupported']} | {doc_share_str} | {wall_str} | {r['distribution']} |")
    print("=" * 110)

    print("\n" + "=" * 110)
    print("ROZBICIE CZASU WYKONANIA (TIMING BREAKDOWN):")
    print("=" * 110)
    print("| Bieg | Wyszukiwanie (s) | Pobieranie (s) | Ekstrakcja (s) | Dekompozycja (s) | Agregacja (s) | Całkowity wall time (s) |")
    print("|------|------------------|----------------|----------------|------------------|---------------|--------------------------|")
    for r in results:
        print(f"| {r['run']} | {r['time_search']:.2f} | {r['time_fetch']:.2f} | {r['time_extraction']:.2f} | {r['time_decomposition']:.2f} | {r['time_aggregation']:.4f} | {r['wall_time']:.2f} |")
    print("=" * 110)

    # Statistics
    valid_times = [r['wall_time'] for r in results if r['wall_time'] > 0]
    if valid_times:
        import statistics
        med_wall = statistics.median(valid_times)
        worst_wall = max(valid_times)
        best_wall = min(valid_times)
        print(f"\nSTATYSTYKI CZASU CAŁKOWITEGO ({len(valid_times)} udanych biegów):")
        print(f"- Mediana czasu całkowitego: {med_wall:.2f} s")
        print(f"- Najgorszy przypadek (worst-case): {worst_wall:.2f} s")
        print(f"- Najlepszy przypadek (best-case): {best_wall:.2f} s")

    valid_extract = [r['time_extraction'] for r in results if r['time_extraction'] > 0]
    valid_decomp = [r['time_decomposition'] for r in results if r['time_decomposition'] > 0]
    if valid_extract and valid_decomp:
        import statistics
        print(f"- Mediana ekstrakcji dowodów: {statistics.median(valid_extract):.2f} s")
        print(f"- Mediana dekompozycji scenariuszy: {statistics.median(valid_decomp):.2f} s")


if __name__ == "__main__":
    asyncio.run(main())
