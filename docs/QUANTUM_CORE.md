# QUANTUM_CORE.md — Quantum Algorithm Module

**Status:** IMPLEMENTED & TESTED (v2.0) · **Last updated:** 2026-09-13 (Phase F & I Verification)

---

## Purpose

The Quantum Core is an obligatory architectural component of YourQuantum.
Its use on any specific task is NOT obligatory — if a classical method produces
a better result within the given budget, the classical result wins.

---

## Implemented Capabilities (Phase F)

| Capability | Status | Implementation Reference |
|-----------|--------|-------------------------|
| Complex amplitudes | **TESTED** | `backend/domain/qaoa_engine.py` (Qiskit Aer statevector & sampler) |
| State preparation | **TESTED** | Uniform superposition $|+\rangle^{\otimes n}$, Warm-started continuous relaxation seeding |
| State evolution | **TESTED** | Alternating phase and mixer operators ($e^{-i \gamma H_C}$, $e^{-i \beta H_M}$) |
| Circuit composition | **TESTED** | Parametric circuits with depth, gate count, and telemetry tracking |
| Noise model simulation | **TESTED** | `backend/domain/qaoa_engine.py` — AerSimulator with depolarizing and amplitude damping |
| Measurement sampling | **TESTED** | Configurable shots (1024–8192) with sample bitstring distribution |
| Variational optimisation | **TESTED** | Multi-start classical parameter optimization (COBYLA, Nelder-Mead) |
| QUBO/Ising compilation | **TESTED** | `backend/domain/qubo_compiler.py` — Problem IR $\to Q$-matrix $\to (h, J)$ spins |
| Multi-Lever DESIGN QUBO | **TESTED** | `backend/domain/design_qubo.py` — $H_{\text{cost}} + H_{\text{one-hot}} + H_{\text{excl}}$, energy gap proof |
| Quantum Evidence Validator | **TESTED** | `backend/domain/quantum_evidence.py` — Verifies physical execution evidence before publication |
| QPU connectivity stub | **TESTED** | `backend/domain/qpu_adapter.py` — Explicit credentials gate, no simulated result passed off as QPU |

---

## Execution Path

```
Problem IR (CHOICE / ALLOCATION / DESIGN)
  │
  ▼
QUBO/Ising Encoder
  │  Produces: Q matrix (QUBO) or h, J vectors (Ising)
  │  Validates: penalty calibration, energy gap > 0 for feasible states
  ▼
Cost Operator Builder
  │  Produces: Cost Hamiltonian $H_C = \sum h_i Z_i + \sum J_{ij} Z_i Z_j$
  ▼
Circuit Composer (QAOA)
  │  Produces: Parametric quantum circuit with $p$ layers
  ▼
Execution Engine ─────────────────────────────────────────┐
  │                                                        │
  ├─ Ideal Simulator (Qiskit Aer statevector / sampler)    │
  ├─ Noise Simulator (AerSimulator with Depolarizing/Kraus)│
  └─ QPU Adapter (Stub requiring IBM/Braket credentials)   │
                                                           │
  ◄──────────────────────────────────────────────────────┘
  │  Produces: raw bitstrings + counts + telemetry record
  ▼
Quantum Evidence Validator (F1 Gate)
  │  Validates: circuit_depth > 0, gate_count > 0, shots > 0
  │  Rejects: empty telemetry or ungrounded claimed quantum origin
  ▼
Decoder
  │  Decodes bitstrings $\to$ Problem IR variable assignment
  ▼
Independent Verifier (see VERIFICATION.md)
  │  Validates all constraints, recomputes objective, checks limitations
  ▼
Result with cryptographic SHA-256 audit passport and honest CPU simulation disclaimer
```

---

## Execution Modes & Honest Terminology

| Mode | Real Backend | Telemetry / Publication | Disclaimer Enforced |
|------|--------------|-------------------------|---------------------|
| Ideal Simulation | Qiskit Aer on CPU | `source: QUANTUM_CIRCUIT_SIMULATION` | "Obliczenia symulowane na klasycznym CPU" |
| Noise Simulation | Aer with noise models | `source: QUANTUM_CIRCUIT_SIMULATION` | "Symulacja z modelem szumu (depolaryzacja)" |
| Hardware QPU | Physical QPU | `source: PHYSICAL_QPU_EXECUTION` | Only with valid hardware job ID & certificate |

### Terminology Rules (Non-Negotiable)
- **DO NOT** call Aer simulation "quantum computation" — call it "quantum circuit simulation on classical CPU".
- **DO NOT** call a candidate list "superposition".
- **DO NOT** call parameter updates "quantum interference".
- **DO NOT** claim quantum advantage over CP-SAT on discrete instances without empirical benchmark JSON evidence.
