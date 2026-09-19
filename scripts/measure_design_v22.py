#!/usr/bin/env python3
"""
scripts/measure_design_v22.py — 10-run production measurement for Prompt V22 (DESIGN class grounded cells).
Targets live production: https://yourquantum.pl/api/v1/cognitive/intake
Query: "Jaki system ochrony zdrowia byłby najlepszy w Polsce w 2027 roku?"
"""
from __future__ import annotations

import json
import logging
import os
import statistics
import sys
import time
import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("measure_v22")

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
            "cells_missing_quote": 0,
            "cells_with_string_null_unit": 0,
            "duplicate_evidence_keys": 0,
            "empty_levers_count": 0,
            "coverage_percent": 0.0,
            "ranking_withheld": True,
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
            "cells_missing_quote": 0,
            "cells_with_string_null_unit": 0,
            "duplicate_evidence_keys": 0,
            "empty_levers_count": 0,
            "coverage_percent": 0.0,
            "ranking_withheld": True,
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
    cells_missing_quote = 0
    cells_with_string_null_unit = 0
    assigned_keys = set()
    duplicate_keys = 0
    sources = set()

    empty_levers = 0
    for l in levers:
        l_id = l.get("id")
        l_cells = 0
        l_data = score_matrix.get(l_id, {})
        for o_id, o_data in l_data.items():
            for c_id, cell in o_data.items():
                val = cell.get("value")
                prov = cell.get("provenance")
                unit = cell.get("unit")
                quote = cell.get("quote")
                c_start = cell.get("char_start")
                c_end = cell.get("char_end")
                s_url = cell.get("source_ref")

                if unit == "null" or unit == "None":
                    cells_with_string_null_unit += 1

                if prov == "assumed":
                    assumed_cells += 1

                if val is not None:
                    doc_cells += 1
                    l_cells += 1
                    if s_url:
                        sources.add(s_url)

                    # Check quote presence and offsets for web_sourced
                    if prov == "web_sourced":
                        if not quote or c_start is None or c_end is None:
                            cells_missing_quote += 1

                        # Check duplicate (url, quote)
                        ev_key = (s_url, quote)
                        if ev_key in assigned_keys:
                            duplicate_keys += 1
                        assigned_keys.add(ev_key)
                else:
                    empty_cells += 1

        if l_cells == 0:
            empty_levers += 1

    ds = data.get("design_synthesis") or {}
    coverage = ds.get("coverage_percentage", 0.0)
    ranking_withheld = ds.get("ranking_withheld", False)
    ranking_reason = ds.get("ranking_withheld_reason")
    indistinguishable = ds.get("indistinguishable_variants") or []

    telemetry = data.get("telemetry") or {}
    rejected_off_topic = telemetry.get("design_cells_rejected_off_topic", 0)
    rejected_duplicate = telemetry.get("design_cells_rejected_duplicate", 0)

    logger.info(
        "Run %d complete: time=%.2fs, class=%s, doc_cells=%d, empty_cells=%d, empty_levers=%d, cov=%.1f%%, ranking_withheld=%s, dup_keys=%d, off_topic_rej=%d",
        run_idx, wall_time, problem_class, doc_cells, empty_cells, empty_levers, coverage, ranking_withheld, duplicate_keys, rejected_off_topic
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
        "cells_missing_quote": cells_missing_quote,
        "cells_with_string_null_unit": cells_with_string_null_unit,
        "duplicate_evidence_keys": duplicate_keys,
        "empty_levers_count": empty_levers,
        "coverage_percent": coverage,
        "ranking_withheld": ranking_withheld,
        "ranking_withheld_reason": ranking_reason,
        "indistinguishable_variants": indistinguishable,
        "telemetry_rejected_off_topic": rejected_off_topic,
        "telemetry_rejected_duplicate": rejected_duplicate,
        "sources": sorted(list(sources)),
        "sources_count": len(sources),
    }


def main():
    print(f"=== MEASURING PROMPT V22 ON PRODUCTION: {URL} ===")
    print(f"Query: {QUERY}")

    results = []
    with httpx.Client() as client:
        for idx in range(1, 11):
            res = run_single(client, idx)
            results.append(res)
            # Short sleep between runs
            if idx < 10:
                time.sleep(2)

    os.makedirs("docs", exist_ok=True)
    with open("docs/measurement_v22_raw.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    times = [r["wall_time"] for r in results if r["status"] == 200]
    docs = [r["documented_cells"] for r in results if r["status"] == 200]
    assumed = [r["assumed_cells"] for r in results if r["status"] == 200]
    missing_quote = [r["cells_missing_quote"] for r in results if r["status"] == 200]
    string_null = [r["cells_with_string_null_unit"] for r in results if r["status"] == 200]
    duplicates = [r["duplicate_evidence_keys"] for r in results if r["status"] == 200]
    empty_levers = [r["empty_levers_count"] for r in results if r["status"] == 200]
    coverages = [r["coverage_percent"] for r in results if r["status"] == 200]
    withheld_count = sum(1 for r in results if r.get("ranking_withheld") is True)

    print("\n=== SUMMARY V22 ===")
    print(f"Runs completed: {len(results)} (successful: {len(times)})")
    if times:
        print(f"Wall time: min={min(times):.2f}s, median={statistics.median(times):.2f}s, max={max(times):.2f}s, mean={statistics.mean(times):.2f}s")
        print(f"Documented cells per run: min={min(docs)}, median={statistics.median(docs)}, max={max(docs)}")
        print(f"Assumed cells across all runs: {sum(assumed)} (MUST BE 0)")
        print(f"Cells missing quote/char offsets: {sum(missing_quote)} (MUST BE 0)")
        print(f"Cells with string 'null' unit: {sum(string_null)} (MUST BE 0)")
        print(f"Duplicate (url, quote) cells: {sum(duplicates)} (MUST BE 0)")
        print(f"Empty levers per run: median={statistics.median(empty_levers)}")
        print(f"Coverage %: min={min(coverages):.1f}%, median={statistics.median(coverages):.1f}%, max={max(coverages):.1f}%")
        print(f"Ranking withheld runs: {withheld_count} / {len(times)}")


if __name__ == "__main__":
    main()
