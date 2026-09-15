#!/usr/bin/env python3
"""
scripts/bench_enumeration.py

Benchmark pomiarowy dla _independent_small_n_enumeration w IndependentVerifier.
Mierzy czas ściankowy dla n in {16, 18, 20, 22, 24} na syntetycznym zadaniu binarnym
o realistycznej strukturze ograniczeń (problem plecakowy z ograniczeniem sumy ważonej).
"""

from __future__ import annotations

import os
import platform
import statistics
import sys
import time
from datetime import datetime, timezone
from typing import Dict, List, Tuple

# Ensure repo root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.domain.problem_ir import (
    Constraint,
    ConstraintType,
    ExprNode,
    ExpressionRegistry,
    Objective,
    ObjectiveDirection,
    ProblemIR,
    Variable,
    VariableDomain,
)
from backend.verifier.verifier import IndependentVerifier


def build_synthetic_knapsack_ir(n: int) -> ProblemIR:
    """
    Tworzy syntetyczne zadanie optymalizacji binarnej o realistycznej strukturze:
    Zmienne: x_0, ..., x_{n-1} in {0, 1}
    Cel: min sum_{i} c_i * x_i (gdzie c_i = (i % 7) + 1)
    Ograniczenie 1 (plecakowe/pojemnościowe): sum_{i} w_i * x_i >= W (gdzie w_i = (i % 5) + 1, W = sum(w_i) / 2)
    Ograniczenie 2 (kardynalność minimalna): sum_{i} x_i >= 1
    """
    reg = ExpressionRegistry()
    variables = []
    obj_terms = []
    w_terms = []
    card_terms = []

    weights = []
    for i in range(n):
        vid = f"x_{i}"
        variables.append(Variable(id=vid, name=vid, domain=VariableDomain.BINARY))

        c_val = float((i % 7) + 1)
        w_val = float((i % 5) + 1)
        weights.append(w_val)

        # Nodes for x_i, c_i, w_i
        reg.add(ExprNode(id=f"v_{vid}", op="var", value=vid))
        reg.add(ExprNode(id=f"c_{i}", op="const", value=c_val))
        reg.add(ExprNode(id=f"w_{i}", op="const", value=w_val))

        # Terms
        reg.add(ExprNode(id=f"obj_term_{i}", op="mul", children=[f"c_{i}", f"v_{vid}"]))
        reg.add(ExprNode(id=f"w_term_{i}", op="mul", children=[f"w_{i}", f"v_{vid}"]))

        obj_terms.append(f"obj_term_{i}")
        w_terms.append(f"w_term_{i}")
        card_terms.append(f"v_{vid}")

    # Objective node: sum of c_i * x_i
    reg.add(ExprNode(id="obj_sum", op="sum", children=obj_terms))

    # Constraint 1: sum(w_i * x_i) >= W
    target_W = sum(weights) / 2.0
    reg.add(ExprNode(id="c1_lhs", op="sum", children=w_terms))
    reg.add(ExprNode(id="c1_rhs", op="const", value=target_W))

    # Constraint 2: sum(x_i) >= 1
    reg.add(ExprNode(id="c2_lhs", op="sum", children=card_terms))
    reg.add(ExprNode(id="c2_rhs", op="const", value=1.0))

    return ProblemIR(
        id=f"bench_knapsack_n{n}",
        description_raw=f"Synthetic binary benchmark problem n={n}",
        description_formalised=f"Synthetic binary benchmark problem n={n}",
        variables=variables,
        expressions=reg,
        objectives=[
            Objective(
                id="primary_obj",
                direction=ObjectiveDirection.MINIMIZE,
                expression_id="obj_sum",
            )
        ],
        constraints=[
            Constraint(
                id="knapsack_bound",
                type=ConstraintType.INEQUALITY_GE,
                lhs_expression_id="c1_lhs",
                rhs_expression_id="c1_rhs",
                hard=True,
            ),
            Constraint(
                id="min_one_item",
                type=ConstraintType.INEQUALITY_GE,
                lhs_expression_id="c2_lhs",
                rhs_expression_id="c2_rhs",
                hard=True,
            ),
        ],
        approved=True,
        approved_at=datetime.now(timezone.utc),
    )


def run_single_benchmark(n: int, runs: int = 3, timeout_per_run: float = 60.0) -> List[float]:
    problem = build_synthetic_knapsack_ir(n)
    verifier = IndependentVerifier(problem)
    primary = problem.objectives[0]

    durations: List[float] = []
    print(f"--- Pomiar dla n = {n} (liczba powtórzeń: {runs}) ---")
    for r in range(runs):
        start_time = time.perf_counter()
        best_obj, gap, proven, note = verifier._independent_small_n_enumeration(
            problem.variables,
            primary,
            is_min=True,
            objective_value=100.0,
        )
        elapsed = time.perf_counter() - start_time
        durations.append(elapsed)
        print(f"  Przebieg {r + 1}/{runs}: {elapsed:.4f} s (best_obj={best_obj}, proven={proven})")

        # Jeśli pojedynczy przebieg przekracza drastycznie budżet (np. > 30s), nie ma sensu zamrażać maszyny
        if elapsed > timeout_per_run:
            print(f"  [UWAGA] Pojedynczy przebieg {elapsed:.2f}s przekroczył limit awaryjny {timeout_per_run}s.")
            break

    return durations


def main():
    sizes = [16, 18, 20, 22, 24]
    time_budget = 2.0  # sekundy

    print("==================================================================")
    print("YOURQUANTUM: BENCHMARK ENUMERACJI NIEZALEŻNEJ (scripts/bench_enumeration.py)")
    print(f"Data: {datetime.now(timezone.utc).isoformat()}")
    print(f"System: {platform.system()} {platform.release()} ({platform.machine()})")
    print(f"Python: {platform.python_version()} ({platform.python_implementation()})")
    cpu_info = platform.processor() or "Unknown CPU"
    print(f"Procesor / Model: {cpu_info}")
    print(f"Budżet czasu mediany: {time_budget:.2f} s")
    print("==================================================================")

    results: Dict[int, Dict[str, float]] = {}
    optimal_threshold = 16

    for n in sizes:
        durations = run_single_benchmark(n, runs=3)
        med = statistics.median(durations)
        mean_val = statistics.mean(durations)
        min_val = min(durations)
        max_val = max(durations)
        results[n] = {
            "median": med,
            "mean": mean_val,
            "min": min_val,
            "max": max_val,
            "runs": len(durations),
        }
        print(f"-> Wynik dla n={n}: mediana={med:.4f} s, min={min_val:.4f} s, max={max_val:.4f} s")

        if med <= time_budget:
            optimal_threshold = n
        else:
            print(f"-> Mediana {med:.4f} s przekracza budżet {time_budget:.2f} s dla n={n}.")
            # Jeżeli n=18 już drastycznie przekracza budżet (>10s), n=20 zajęłoby ~1 minutę, a n=24 ponad kwadrans
            if n >= 18:
                print(f"-> Przerwanie pomiarów dla n >= 20 (złożoność 2^{n+2} przekracza dopuszczalny czas wykonania).")
                break

    print("\n==================================================================")
    print("PODSUMOWANIE POMIARÓW")
    print("------------------------------------------------------------------")
    print(f"{'n':<6} | {'Mediana [s]':<14} | {'Min [s]':<10} | {'Max [s]':<10} | {'Liczba prób':<12} | {'W budżecie (<=2.0s)'}")
    print("-" * 75)
    for n, data in results.items():
        in_budget = "TAK" if data["median"] <= time_budget else "NIE"
        print(f"{n:<6} | {data['median']:<14.4f} | {data['min']:<10.4f} | {data['max']:<10.4f} | {data['runs']:<12} | {in_budget}")
    print("-" * 75)
    print(f"WYNIK: Nowy wyznaczony próg MAX_ENUMERATION_VARS = {optimal_threshold}")
    print("==================================================================")


if __name__ == "__main__":
    main()
