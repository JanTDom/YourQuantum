"""
YourQuantum — Multi-Criteria Decision Matrix & Analytical Break-Even Engine
Replaces subjective LLM score assignments with deterministic, user-weighted
utility modeling, rigorous normalization, and analytical sensitivity shifts.
"""
from __future__ import annotations

import math
from typing import Any, Literal
from pydantic import BaseModel, Field

from backend.domain.decision_case import DecisionCase, Criterion, Option, ScoredValue


class BreakEvenShift(BaseModel):
    criterion_id: str
    criterion_name: str
    shift_type: Literal["value_shift", "weight_shift"]
    current_value: float
    required_value: float
    absolute_delta: float
    unit: str | None = None
    description: str


class BreakEvenAnalysis(BaseModel):
    winner_option_id: str
    winner_option_title: str
    runner_up_option_id: str
    runner_up_option_title: str
    utility_gap: float
    shifts: list[BreakEvenShift] = Field(default_factory=list)
    summary_pl: str


def calculate_criteria_weights(case: DecisionCase) -> dict[str, float]:
    """
    Derive criteria weights exclusively from user preferences:
    - User explicit Criterion.weight (1.0 default)
    - If priority tokens are selected by the user, criteria matching tokens receive a multiplier (2.0)
    Never uses subjective LLM rankings.
    """
    weights: dict[str, float] = {}
    selected_tokens_lower = {t.strip().lower() for t in case.selected_priority_tokens}

    for crit in case.criteria:
        base_weight = max(0.01, float(crit.weight))
        crit_name_lower = crit.name.lower()
        crit_id_lower = crit.id.lower()

        # Check if user selected priority token matching this criterion
        is_prioritized = any(
            tok in crit_name_lower or tok in crit_id_lower or crit_name_lower in tok
            for tok in selected_tokens_lower
        )
        multiplier = 2.0 if is_prioritized else 1.0
        weights[crit.id] = base_weight * multiplier

    # Normalize weights so they sum to 1.0 (or equal distribution if sum is zero)
    total = sum(weights.values())
    if total > 0:
        return {cid: w / total for cid, w in weights.items()}
    uniform = 1.0 / max(1, len(case.criteria))
    return {crit.id: uniform for crit in case.criteria}


def normalize_matrix(case: DecisionCase) -> dict[str, dict[str, float]]:
    """
    Perform min-max normalization per criterion to map all metrics into [0.0, 1.0].
    - maximize: (v - min) / (max - min)
    - minimize: (max - v) / (max - min)
    If min == max, all options score 1.0 on this criterion.
    """
    normalized: dict[str, dict[str, float]] = {opt.id: {} for opt in case.options}

    for crit in case.criteria:
        cid = crit.id
        vals: list[float] = []
        for opt in case.options:
            cell = case.score_matrix.get(opt.id, {}).get(cid)
            if cell is not None:
                vals.append(float(cell.value))
            elif opt.attributes.get(cid) is not None:
                try:
                    vals.append(float(opt.attributes[cid]))
                except (ValueError, TypeError):
                    pass

        if not vals:
            for opt in case.options:
                normalized[opt.id][cid] = 0.5
            continue

        min_v = min(vals)
        max_v = max(vals)
        span = max_v - min_v

        for opt in case.options:
            cell = case.score_matrix.get(opt.id, {}).get(cid)
            raw_val: float
            if cell is not None:
                raw_val = float(cell.value)
            elif opt.attributes.get(cid) is not None:
                try:
                    raw_val = float(opt.attributes[cid])
                except (ValueError, TypeError):
                    raw_val = min_v
            else:
                raw_val = min_v

            if span <= 1e-9:
                score = 1.0
            elif crit.direction == "maximize":
                score = (raw_val - min_v) / span
            else:
                score = (max_v - raw_val) / span

            normalized[opt.id][cid] = max(0.0, min(1.0, score))

    return normalized


def compute_option_utilities(case: DecisionCase) -> dict[str, float]:
    """
    Calculate weighted utility U_o = sum_k (w_k * norm_k(v_{o,k})) for each option.
    """
    weights = calculate_criteria_weights(case)
    norm_scores = normalize_matrix(case)
    utilities: dict[str, float] = {}

    for opt in case.options:
        u = sum(weights.get(cid, 0.0) * norm_scores.get(opt.id, {}).get(cid, 0.0) for cid in weights)
        utilities[opt.id] = round(u, 6)

    return utilities


def calculate_analytical_break_even(case: DecisionCase) -> BreakEvenAnalysis | None:
    """
    DEC-015: Analytically compute minimal parameter shifts needed for runner-up to overtake winner.
    Computes exact required shifts without LLM guessing.
    """
    if len(case.options) < 2 or not case.criteria:
        return None

    utilities = compute_option_utilities(case)
    sorted_options = sorted(case.options, key=lambda o: utilities.get(o.id, 0.0), reverse=True)
    winner = sorted_options[0]
    runner_up = sorted_options[1]

    u_win = utilities.get(winner.id, 0.0)
    u_run = utilities.get(runner_up.id, 0.0)
    gap = u_win - u_run

    if gap <= 1e-9:
        return BreakEvenAnalysis(
            winner_option_id=winner.id,
            winner_option_title=winner.title,
            runner_up_option_id=runner_up.id,
            runner_up_option_title=runner_up.title,
            utility_gap=0.0,
            shifts=[],
            summary_pl=f"Opcje '{winner.title}' oraz '{runner_up.title}' uzyskują zbliżoną ocenę użyteczności ({u_win:.2f}).",
        )

    weights = calculate_criteria_weights(case)
    norm_scores = normalize_matrix(case)
    shifts: list[BreakEvenShift] = []

    # 1. Parameter / Value sensitivity per criterion
    for crit in case.criteria:
        cid = crit.id
        w_k = weights.get(cid, 0.0)
        if w_k <= 1e-6:
            continue

        vals = []
        for opt in case.options:
            c = case.score_matrix.get(opt.id, {}).get(cid)
            if c is not None:
                vals.append(float(c.value))
        if not vals:
            continue
        min_v = min(vals)
        max_v = max(vals)
        span = max_v - min_v

        runner_cell = case.score_matrix.get(runner_up.id, {}).get(cid)
        current_raw = float(runner_cell.value) if runner_cell is not None else min_v

        delta_score = gap / w_k
        if span > 1e-9:
            raw_delta = delta_score * span
            if crit.direction == "maximize":
                req_val = current_raw + raw_delta
                desc = (
                    f"Opcja '{runner_up.title}' wygrałaby, gdyby jej {crit.name.lower()} "
                    f"wzrosła o {raw_delta:.2f}{f' {crit.unit}' if crit.unit else ''} (do poziomu {req_val:.2f})."
                )
            else:
                req_val = current_raw - raw_delta
                desc = (
                    f"Opcja '{runner_up.title}' wygrałaby, gdyby jej {crit.name.lower()} "
                    f"spadła o {raw_delta:.2f}{f' {crit.unit}' if crit.unit else ''} (do poziomu {req_val:.2f})."
                )

            shifts.append(
                BreakEvenShift(
                    criterion_id=cid,
                    criterion_name=crit.name,
                    shift_type="value_shift",
                    current_value=current_raw,
                    required_value=req_val,
                    absolute_delta=raw_delta,
                    unit=crit.unit,
                    description=desc,
                )
            )

        # 2. Weight sensitivity: if runner-up is already better on this criterion than winner!
        s_run = norm_scores.get(runner_up.id, {}).get(cid, 0.0)
        s_win = norm_scores.get(winner.id, {}).get(cid, 0.0)
        score_diff = s_run - s_win

        if score_diff > 1e-4:
            req_w = w_k + (gap / score_diff)
            w_delta = req_w - w_k
            shifts.append(
                BreakEvenShift(
                    criterion_id=cid,
                    criterion_name=crit.name,
                    shift_type="weight_shift",
                    current_value=w_k,
                    required_value=req_w,
                    absolute_delta=w_delta,
                    unit="waga",
                    description=(
                        f"Opcja '{runner_up.title}' wygrałaby, gdyby waga kryterium '{crit.name}' "
                        f"wzrosła z {w_k:.2f} do {req_w:.2f} (ponieważ w tym kryterium przewyższa opcję zwycięską)."
                    ),
                )
            )

    summary_parts: list[str] = []
    if shifts:
        top_shift = shifts[0]
        summary_parts.append(top_shift.description)
        if len(shifts) > 1:
            summary_parts.append(shifts[1].description)
        summary_pl = " ".join(summary_parts)
    else:
        summary_pl = f"Przewaga opcji '{winner.title}' nad '{runner_up.title}' wynosi {gap:.2f} pkt użyteczności."

    return BreakEvenAnalysis(
        winner_option_id=winner.id,
        winner_option_title=winner.title,
        runner_up_option_id=runner_up.id,
        runner_up_option_title=runner_up.title,
        utility_gap=gap,
        shifts=shifts,
        summary_pl=summary_pl,
    )
