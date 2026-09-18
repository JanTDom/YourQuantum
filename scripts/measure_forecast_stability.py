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
        "distribution": dist_str,
        "dominant_scenario": forecast_data.get("dominant_scenario_id", ""),
        "dominant_prob": telemetry.get("dominant_probability", 0),
        "wall_time": telemetry.get("intake_wall_time_seconds", 0.0),
    }


async def main():
    query = "Czy Rosja do końca tego roku napadnie na Polskę?"
    print(f"Rozpoczynam pomiar stabilności (5 biegów) dla zapytania: {query}")
    
    adapter = GeminiCognitiveAdapter()
    engine = ActiveInferenceOrchestrator(reasoning_port=adapter)
    results = []
    
    for i in range(1, 6):
        run_name = f"Bieg {chr(64 + i)}"  # A, B, C, D, E
        print(f"\n>>> Wykonuję {run_name}...")
        try:
            r = await run_single(engine, run_name, query)
            results.append(r)
            print(f"    Wynik: cytaty={r['quotes_verified']}, aktywne={r['active_premises']}, proposed={r['impacts_proposed']}, accepted={r['impacts_accepted']}, odrzucone={r['impact_rejected_unsupported']}, rozkład={r['distribution']}")
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
                "distribution": f"BŁĄD: {e}",
                "dominant_prob": 0,
                "wall_time": 0,
            })

    print("\n" + "=" * 90)
    print("TABELA WYNIKÓW POMIARU STABILNOŚCI:")
    print("=" * 90)
    print("| Bieg | Zweryfikowane cytaty | Aktywne przesłanki | impacts_proposed | impacts_accepted | impact_rejected_unsupported | Rozkład |")
    print("|------|----------------------|--------------------|------------------|------------------|-----------------------------|---------|")
    for r in results:
        print(f"| {r['run']} | {r['quotes_verified']} | {r['active_premises']} | {r['impacts_proposed']} | {r['impacts_accepted']} | {r['impact_rejected_unsupported']} | {r['distribution']} |")
    print("=" * 90)


if __name__ == "__main__":
    asyncio.run(main())
