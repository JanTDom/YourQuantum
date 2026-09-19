#!/usr/bin/env python3
"""
scripts/measure_design_v21.py — 10-run production measurement for Prompt V21 (DESIGN class evidence pipeline).
Targets live production: https://yourquantum.pl/api/v1/cognitive/intake
Query: "Jaki system ochrony zdrowia byłby najlepszy w Polsce w 2027 roku?"
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import statistics
import sys
import time
import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("measure_v21")

URL = "https://yourquantum.pl/api/v1/cognitive/intake"
QUERY = "Jaki system ochrony zdrowia byłby najlepszy w Polsce w 2027 roku?"


def run_single(client: httpx.Client, run_idx: int) -> dict:
    logger.info("Starting Run %d / 10...", run_idx)
    t0 = time.monotonic()
    try:
        resp = client.post(URL, json={"query": QUERY}, timeout=200.0)
    except Exception as exc:
        wall_time = round(time.monotonic() - t0, 2)
        logger.error("Run %d exception: %s", run_idx, exc)
        return {
            "run": run_idx,
            "status": "TIMEOUT" if "timeout" in str(exc).lower() else "ERROR",
            "wall_time": wall_time,
            "problem_class": "ERROR",
            "documented_cells": 0,
            "empty_cells": 0,
            "assumed_cells": 0,
            "sources": [],
            "error": str(exc)[:200],
        }

    wall_time = round(time.monotonic() - t0, 2)
    status_code = resp.status_code
    if status_code != 200:
        logger.error("Run %d failed with status %d: %s", run_idx, status_code, resp.text[:200])
        return {
            "run": run_idx,
            "status": status_code,
            "wall_time": wall_time,
            "problem_class": "ERROR",
            "documented_cells": 0,
            "empty_cells": 0,
            "assumed_cells": 0,
            "sources": [],
            "error": resp.text[:200],
        }

    data = resp.json()
    problem_class = data.get("problem_class")
    dp = data.get("design_problem") or {}
    levers = dp.get("levers") or []
    criteria = dp.get("criteria") or []
    score_matrix = dp.get("score_matrix") or {}

    doc_cells = 0
    empty_cells = 0
    assumed_cells = 0
    sources = set()

    total_possible_cells = len(levers) * 3 * len(criteria)  # approximate
    actual_cells = 0

    for l_id, l_data in score_matrix.items():
        for o_id, o_data in l_data.items():
            for c_id, cell in o_data.items():
                actual_cells += 1
                prov = cell.get("provenance")
                val = cell.get("value")
                if prov == "assumed":
                    assumed_cells += 1
                if val is not None:
                    doc_cells += 1
                    if cell.get("source_ref"):
                        sources.add(cell.get("source_ref"))
                else:
                    empty_cells += 1

    ds = data.get("design_synthesis") or {}

    logger.info(
        "Run %d complete: time=%.2fs, class=%s, doc_cells=%d, empty_cells=%d, assumed=%d, sources=%d",
        run_idx, wall_time, problem_class, doc_cells, empty_cells, assumed_cells, len(sources)
    )

    return {
        "run": run_idx,
        "status": status_code,
        "wall_time": wall_time,
        "problem_class": problem_class,
        "levers_count": len(levers),
        "criteria_count": len(criteria),
        "documented_cells": doc_cells,
        "empty_cells": empty_cells,
        "assumed_cells": assumed_cells,
        "sources": sorted(list(sources)),
        "sources_count": len(sources),
    }


def main():
    print(f"=== MEASURING PROMPT V21 ON PRODUCTION: {URL} ===")
    print(f"Query: {QUERY}")

    results = []
    with httpx.Client() as client:
        for idx in range(1, 11):
            res = run_single(client, idx)
            results.append(res)
            # Short sleep between runs
            if idx < 10:
                time.sleep(2)

    with open("docs/measurement_v21_raw.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    times = [r["wall_time"] for r in results if r["status"] == 200]
    docs = [r["documented_cells"] for r in results if r["status"] == 200]
    assumed = [r["assumed_cells"] for r in results if r["status"] == 200]

    print("\n=== SUMMARY ===")
    print(f"Runs completed: {len(results)} (successful: {len(times)})")
    if times:
        print(f"Wall time: min={min(times):.2f}s, median={statistics.median(times):.2f}s, max={max(times):.2f}s, mean={statistics.mean(times):.2f}s")
        print(f"Documented cells per run: min={min(docs)}, median={statistics.median(docs)}, max={max(docs)}")
        print(f"Assumed cells across all runs: {sum(assumed)} (MUST BE 0)")


if __name__ == "__main__":
    main()
