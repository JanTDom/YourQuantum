---
name: yq-design-synthesis
description: Procedure for multi-lever architectural synthesis, lever decomposition, Pareto frontier analysis, and evidence-grounded option design.
---

# YQ-DESIGN-SYNTHESIS: Multi-Lever Architectural Synthesis

Use this skill when tackling complex architectural problems that require designing a comprehensive solution
rather than choosing between isolated options (e.g., healthcare system design, tax reform, logistics network redesign).

## Core Principles

1. **System Synthesis over Trivial Choice:**
   Decompose the open-ended question into 3–6 orthogonal **Design Levers** (`DesignLever`), each with 2–6 mutually exclusive **Lever Options** (`LeverOption`).
2. **Every Lever Option Requires Evidence:**
   No imaginary options. Each option must have a real-world evidence reference (`evidence_ref`) or be explicitly marked `is_hypothetical = True`.
3. **Zero Fabricated Synergies:**
   Synergies between levers represent quadratic objective terms. **Every non-zero synergy MUST cite an empirical source or an explicit user assumption.** Silent default synergy is strictly 0.0.
4. **Pareto Frontier over Single "Miracle" Answer:**
   Always compute and present the Pareto frontier across primary criteria (e.g. cost vs quality vs equity). Show the user the trade-offs: what is sacrificed when prioritizing one dimension over another.
5. **Model-Optimal Truth:**
   Always label results honestly: *"Model-optimal, not world-optimal"* (the result is optimal given the formalised criteria, weights, and constraints, not an absolute prophecy).
