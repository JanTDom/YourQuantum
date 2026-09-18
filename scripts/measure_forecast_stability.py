#!/usr/bin/env python3
"""
scripts/measure_forecast_stability.py — Measures stability and reproducibility of forecast results.
Supports live production target (--target https://yourquantum.pl) and local engine (--target local).
Runs 10 consecutive runs on the target query:
"Czy Rosja do końca tego roku napadnie na Polskę?"
Outputs a Markdown table with raw results, telemetry, timing breakdown, and stability metrics.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import statistics
import sys
import time
from unittest.mock import AsyncMock
from dotenv import load_dotenv
import httpx

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

load_dotenv(os.path.join(repo_root, ".env"))
load_dotenv(os.path.join(repo_root, ".env.local"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("stability_test")


async def run_single_remote(client: httpx.AsyncClient, target_url: str, run_id: str, query: str) -> dict:
    url = f"{target_url.rstrip('/')}/api/v1/cognitive/intake"
    t0 = time.monotonic()
    resp = await client.post(url, json={"query": query})
    client_wall_time = round(time.monotonic() - t0, 2)
    resp.raise_for_status()
    data = resp.json()

    forecast_data = data.get("scenario_forecast") or {}
    scenarios = forecast_data.get("scenarios", [])
    premises = forecast_data.get("evidence_premises", [])
    telemetry = forecast_data.get("telemetry", {})

    probs = [f"{float(sc.get('probability', 0.0)) * 100:.1f}%".replace(".", ",") for sc in scenarios]
    dist_str = " / ".join(probs) if probs else "N/A"

    active_premises = [p for p in premises if p.get("is_accepted", False)]

    wall_time = telemetry.get("intake_wall_time_seconds")
    if wall_time is None or wall_time == 0:
        wall_time = client_wall_time

    return {
        "run": run_id,
        "quotes_verified": telemetry.get("web_quotes_verified", 0),
        "active_premises": len(active_premises),
        "total_premises": len(premises),
        "impacts_proposed": telemetry.get("impacts_proposed", 0),
        "impacts_accepted": telemetry.get("impacts_accepted", 0),
        "impact_rejected_unsupported": telemetry.get("impact_rejected_unsupported", 0),
        "impacts_not_proposed_reason": telemetry.get("impacts_not_proposed_reason"),
        "impact_documented_share": float(telemetry.get("impact_documented_share", 0.0)),
        "distribution": dist_str,
        "dominant_scenario": forecast_data.get("dominant_scenario_id", ""),
        "dominant_prob": telemetry.get("dominant_probability", 0),
        "wall_time": float(wall_time),
        "time_search": float(telemetry.get("time_search_seconds", 0.0)),
        "time_fetch": float(telemetry.get("time_fetch_seconds", 0.0)),
        "time_extraction": float(telemetry.get("time_extraction_seconds", 0.0)),
        "time_decomposition": float(telemetry.get("time_decomposition_seconds", 0.0)),
        "time_aggregation": float(telemetry.get("time_aggregation_seconds", 0.0)),
    }


async def run_single_local(engine, run_id: str, query: str) -> dict:
    from backend.domain.cognitive.workspace import GlobalWorkspace

    os.environ["SEARCH_PROVIDER"] = "gemini"
    mock_session = AsyncMock()
    ws = GlobalWorkspace(goal=query, session_id=f"stability_{run_id}")
    res, updated_ws = await engine.run_intake(session=mock_session, query=query, workspace=ws)

    forecast_data = res.scenario_forecast or {}
    scenarios = forecast_data.get("scenarios", [])
    premises = forecast_data.get("evidence_premises", [])
    telemetry = forecast_data.get("telemetry", {})

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
        "impacts_not_proposed_reason": telemetry.get("impacts_not_proposed_reason"),
        "impact_documented_share": float(telemetry.get("impact_documented_share", 0.0)),
        "distribution": dist_str,
        "dominant_scenario": forecast_data.get("dominant_scenario_id", ""),
        "dominant_prob": telemetry.get("dominant_probability", 0),
        "wall_time": float(telemetry.get("intake_wall_time_seconds", 0.0)),
        "time_search": float(telemetry.get("time_search_seconds", 0.0)),
        "time_fetch": float(telemetry.get("time_fetch_seconds", 0.0)),
        "time_extraction": float(telemetry.get("time_extraction_seconds", 0.0)),
        "time_decomposition": float(telemetry.get("time_decomposition_seconds", 0.0)),
        "time_aggregation": float(telemetry.get("time_aggregation_seconds", 0.0)),
    }


async def main():
    parser = argparse.ArgumentParser(description="YourQuantum Forecast Stability Measurement")
    parser.add_argument("--target", default="https://yourquantum.pl", help="Target URL (e.g. https://yourquantum.pl or local)")
    parser.add_argument("--runs", type=int, default=10, help="Number of runs (default: 10)")
    parser.add_argument("--query", default="Czy Rosja do końca tego roku napadnie na Polskę?", help="Query text")
    args = parser.parse_args()

    query = args.query
    num_runs = args.runs
    target = args.target

    print(f"Rozpoczynam pomiar stabilności ({num_runs} biegów)")
    print(f"Target: {target}")
    print(f"Pytanie: '{query}'")

    engine = None
    client = None

    if target.lower() == "local":
        from backend.domain.cognitive.active_inference_engine import ActiveInferenceOrchestrator
        from backend.infrastructure.gemini_cognitive_adapter import GeminiCognitiveAdapter
        adapter = GeminiCognitiveAdapter()
        engine = ActiveInferenceOrchestrator(reasoning_port=adapter)
    else:
        client = httpx.AsyncClient(timeout=180.0, follow_redirects=True)

    results = []

    try:
        for i in range(1, num_runs + 1):
            run_name = f"Bieg {chr(64 + i)}" if i <= 26 else f"Bieg {i}"
            print(f"\n>>> Wykonuję {run_name} ({i}/{num_runs})...")
            try:
                if engine is not None:
                    r = await run_single_local(engine, run_name, query)
                else:
                    r = await run_single_remote(client, target, run_name, query)
                results.append(r)
                reason_str = f" [powód braku: {r['impacts_not_proposed_reason']}]" if r['impacts_not_proposed_reason'] else ""
                print(f"    Wynik: cytaty={r['quotes_verified']}, aktywne={r['active_premises']}, proposed={r['impacts_proposed']}, accepted={r['impacts_accepted']}, doc_share={r['impact_documented_share']}%, czas={r['wall_time']}s{reason_str}, rozkład={r['distribution']}")
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
                    "impacts_not_proposed_reason": f"błąd wykonania: {e}",
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
    finally:
        if client:
            await client.aclose()

    print("\n" + "=" * 135)
    print(f"TABELA WYNIKÓW POMIARU STABILNOŚCI ({num_runs} BIEGÓW NA {target}):")
    print("=" * 135)
    print("| Bieg | Zweryfikowane cytaty | Aktywne przesłanki | impacts_proposed | impacts_accepted | impact_rejected_unsupported | impacts_not_proposed_reason | impact_documented_share | Czas całkowity | Rozkład |")
    print("|------|----------------------|--------------------|------------------|------------------|-----------------------------|-----------------------------|-------------------------|----------------|---------|")
    for r in results:
        doc_share_str = f"{r['impact_documented_share']:.1f}%".replace(".", ",")
        wall_str = f"{r['wall_time']:.2f} s".replace(".", ",")
        reason_val = r.get('impacts_not_proposed_reason') or "—"
        print(f"| {r['run']} | {r['quotes_verified']} | {r['active_premises']} | {r['impacts_proposed']} | {r['impacts_accepted']} | {r['impact_rejected_unsupported']} | {reason_val} | {doc_share_str} | {wall_str} | {r['distribution']} |")
    print("=" * 135)

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
        med_wall = statistics.median(valid_times)
        worst_wall = max(valid_times)
        best_wall = min(valid_times)
        print(f"\nSTATYSTYKI CZASU CAŁKOWITEGO ({len(valid_times)} udanych biegów):")
        print(f"- Mediana czasu całkowitego: {med_wall:.2f} s")
        print(f"- Najgorszy przypadek (worst-case): {worst_wall:.2f} s")
        print(f"- Najlepszy przypadek (best-case): {best_wall:.2f} s")

    # Documented share statistics
    positive_share_runs = [r for r in results if r['impact_documented_share'] > 0]
    all_shares = [r['impact_documented_share'] for r in results]
    print(f"\nSTATYSTYKI UDOKUMENTOWANIA WPŁYWÓW:")
    print(f"- Liczba biegów z impact_documented_share > 0: {len(positive_share_runs)}/{len(results)}")
    if positive_share_runs:
        print(f"- Rozrzut impact_documented_share: min={min(all_shares):.1f}%, max={max(all_shares):.1f}%, średnia={statistics.mean(all_shares):.1f}%")
    else:
        reasons = [r['impacts_not_proposed_reason'] for r in results if r.get('impacts_not_proposed_reason')]
        print(f"- Wszystkie biegi mają impact_documented_share == 0.0%.")
        if reasons:
            from collections import Counter
            counts = Counter(reasons)
            print(f"- Rozkład przyczyn braku propozycji (impacts_not_proposed_reason): {dict(counts)}")


if __name__ == "__main__":
    asyncio.run(main())
