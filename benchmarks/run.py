#!/usr/bin/env python3
"""
YourQuantum — Benchmark Suite Execution Script
Runs empirical benchmarks comparing:
1. OR-Tools CP-SAT (Classical Exact Baseline)
2. QAOA (Ideal Statevector Circuit Simulation)
3. QAOA (Aer Noise Simulation with Depolarizing Channel)

Instances evaluated:
- Healthcare Reform Multi-Lever Design (tests/fixtures/design/healthcare_pl.json)
- Synthetic Binary Allocation Instances (N=4, N=6, N=8, N=10)

Saves JSON reports to benchmarks/results/benchmark_<timestamp>.json
and prints human-readable comparison table adhering to AGENTS.md §7 (Evidence Rule).
"""
from __future__ import annotations

import json
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

# Ensure backend is in python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.domain.problem_classes import DesignProblem
from backend.domain.problem_ir import (
    ComputeBudget, Constraint, ConstraintType, ExprNode, ExpressionRegistry,
    Objective, ObjectiveDirection, ProblemIR, Provenance, Variable, VariableDomain,
)
from backend.solvers.base import ExecutionStatus
from backend.solvers.cpsat import CPSATAdapter
from backend.solvers.quantum.qaoa import QAOAAdapter


def build_synthetic_allocation_problem(n: int, seed: int = 42) -> ProblemIR:
    """
    Builds a synthetic binary allocation problem (Knapsack/Resource Selection)
    with N binary items, deterministic weights and values, and capacity constraint.
    """
    rng = np.random.default_rng(seed + n)
    values = rng.integers(5, 30, size=n).astype(float)
    weights = rng.integers(2, 15, size=n).astype(float)
    capacity = float(weights.sum() * 0.55)

    reg = ExpressionRegistry()
    variables: list[Variable] = []
    val_terms: list[str] = []
    weight_terms: list[str] = []

    for i in range(n):
        vid = f"x_{i}"
        variables.append(
            Variable(
                id=vid,
                name=f"Item {i}",
                domain=VariableDomain.BINARY,
                provenance=Provenance.USER_SUPPLIED,
            )
        )
        reg.add(ExprNode(id=f"v_{vid}", op="var", value=vid))

        # Value term: values[i] * x_i
        vc_id = reg.add(ExprNode(id=f"vc_{i}", op="const", value=values[i]))
        val_terms.append(reg.add(ExprNode(id=f"vterm_{i}", op="mul", children=[vc_id, f"v_{vid}"])))

        # Weight term: weights[i] * x_i
        wc_id = reg.add(ExprNode(id=f"wc_{i}", op="const", value=weights[i]))
        weight_terms.append(reg.add(ExprNode(id=f"wterm_{i}", op="mul", children=[wc_id, f"v_{vid}"])))

    # Objective: Maximize sum(values[i] * x_i)
    obj_sum_id = reg.add(ExprNode(id="obj_sum", op="sum", children=val_terms))
    objective = Objective(
        id="obj_profit",
        name="Maximize Total Profit",
        direction=ObjectiveDirection.MAXIMIZE,
        expression_id=obj_sum_id,
    )

    # Constraint: sum(weights[i] * x_i) <= capacity
    w_sum_id = reg.add(ExprNode(id="weight_sum", op="sum", children=weight_terms))
    cap_id = reg.add(ExprNode(id="cap_const", op="const", value=capacity))
    constraint = Constraint(
        id="capacity_limit",
        type=ConstraintType.INEQUALITY_LE,
        lhs_expression_id=w_sum_id,
        rhs_expression_id=cap_id,
        hard=True,
        description=f"Knapsack capacity limit <= {capacity:.1f}",
    )

    problem = ProblemIR(
        problem_id=f"alloc_n{n}_s{seed}",
        description_raw=f"Synthetic allocation of {n} binary items with capacity limit.",
        description_formalised=f"Maximize profit over {n} binary items subject to total weight <= {capacity:.1f}.",
        version=1,
        variables=variables,
        constraints=[constraint],
        objectives=[objective],
        expressions=reg,
        approved=True,
    )
    return problem


def load_design_problem(fixture_path: str) -> ProblemIR:
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    dp = DesignProblem(**data)
    ir = dp.compile_to_problem_ir()
    ir.approved = True
    return ir


def run_benchmarks() -> dict[str, Any]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    results_dir = Path("benchmarks/results")
    results_dir.mkdir(parents=True, exist_ok=True)

    instances: list[tuple[str, ProblemIR]] = []

    # 1. Healthcare Reform instance
    healthcare_path = Path("tests/fixtures/design/healthcare_pl.json")
    if healthcare_path.exists():
        instances.append(("Healthcare Reform (DESIGN)", load_design_problem(str(healthcare_path))))

    # 2. Synthetic Allocation instances N=4, 6, 8, 10
    for n in (4, 6, 8, 10):
        instances.append((f"Allocation N={n}", build_synthetic_allocation_problem(n)))

    # Solvers to evaluate
    solvers = [
        ("CP-SAT (Classical Exact)", CPSATAdapter()),
        ("QAOA (Ideal Statevector)", QAOAAdapter(mode="ideal_statevector")),
        ("QAOA (Aer Noise Model)", QAOAAdapter(mode="noise_simulation", depolarizing_p1=0.002, depolarizing_p2=0.02)),
    ]

    budget = ComputeBudget(wall_time_seconds=10.0, memory_mb=512.0, quantum_shots=1024)

    benchmark_runs: list[dict[str, Any]] = []

    print(f"\n=======================================================")
    print(f" YourQuantum Empirical Benchmark Suite ({timestamp})")
    print(f" Platform: {platform.system()} {platform.machine()} | Python {platform.python_version()}")
    print(f" Instances: {len(instances)} | Solvers: {len(solvers)}")
    print(f"=======================================================\n")

    for inst_label, problem in instances:
        print(f"--- Running instance: {inst_label} ({len(problem.variables)} vars, {len(problem.constraints)} constraints) ---")
        cpsat_obj: float | None = None

        instance_results: dict[str, Any] = {
            "instance_label": inst_label,
            "n_variables": len(problem.variables),
            "n_constraints": len(problem.constraints),
            "solvers": {},
        }

        for solver_label, solver in solvers:
            t_start = time.perf_counter()
            res = solver.solve(problem, budget)
            elapsed = time.perf_counter() - t_start

            obj_val = res.objective_value
            if "CP-SAT" in solver_label and res.execution_status == ExecutionStatus.COMPLETED:
                cpsat_obj = obj_val

            # Compute relative gap to CP-SAT if both succeeded
            rel_gap: float | None = None
            if cpsat_obj is not None and obj_val is not None:
                rel_gap = round(abs(obj_val - cpsat_obj) / (abs(cpsat_obj) + 1e-9), 4)

            entry: dict[str, Any] = {
                "solver_name": solver.name,
                "solver_version": solver.version,
                "execution_status": res.execution_status.value,
                "math_status": res.math_status.value,
                "objective_value": obj_val,
                "solve_time_seconds": round(elapsed, 4),
                "relative_gap_to_cpsat": rel_gap,
                "ground_state_prob": res.metadata.get("ground_state_prob"),
                "amplification_factor": res.metadata.get("amplification_factor"),
                "n_qubits": res.metadata.get("n_qubits"),
                "circuit_depth": res.metadata.get("circuit_depth"),
            }
            if res.execution_evidence:
                entry["execution_evidence_summary"] = {
                    "backend_name": res.execution_evidence.get("backend_name"),
                    "execution_mode": res.execution_evidence.get("execution_mode"),
                    "shots": res.execution_evidence.get("shots"),
                }

            instance_results["solvers"][solver_label] = entry
            print(f"  [{solver_label[:22]:<22}] status={res.execution_status.value:<9} obj={str(obj_val):<8} time={elapsed:.3f}s amp={str(res.metadata.get('amplification_factor'))}")

        benchmark_runs.append(instance_results)

    output_payload: dict[str, Any] = {
        "benchmark_id": f"bench_{timestamp}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
        },
        "budget": {
            "wall_time_seconds": budget.wall_time_seconds,
            "quantum_shots": budget.quantum_shots,
            "memory_mb": budget.memory_mb,
        },
        "instances_count": len(instances),
        "results": benchmark_runs,
    }

    out_file = results_dir / f"benchmark_{timestamp}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)

    print(f"\n[OK] Benchmark completed. Results saved to: {out_file}\n")
    return output_payload


if __name__ == "__main__":
    run_benchmarks()
