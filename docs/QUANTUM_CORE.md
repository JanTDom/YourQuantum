# QUANTUM_CORE.md — Quantum Algorithm Module

**Status:** PLANNED · **Last updated:** 2026-09-09

---

## Purpose

The Quantum Core is an obligatory architectural component of YourQuantum.
Its use on any specific task is NOT obligatory — if a classical method produces
a better result within the given budget, the classical result wins.

---

## Mandatory Capabilities (to be implemented)

| Capability | Description |
|-----------|-------------|
| Complex amplitudes | State vectors with full complex-number representation |
| State preparation | Arbitrary state initialisation, standard ansätze |
| State evolution | Unitary operators, parametric gates, noise models |
| Circuit composition | Gate-level and higher-level circuit building |
| Interference | Correctly computed from the amplitude arithmetic — not metaphorical |
| Measurement sampling | Projective measurement with configurable shot count |
| Variational optimisation | Parameter optimisation loop (COBYLA, SPSA, Adam) |
| QUBO/Ising compilation | Problem IR → QUBO matrix → Ising Hamiltonian |
| QPU connectivity | Adapter interface for real hardware backends |

---

## Execution Path

```
Problem IR
  │
  ▼
QUBO/Ising Encoder
  │  Produces: Q matrix (QUBO) or h, J vectors (Ising)
  │  Validates: encoding correctness, qubit count
  ▼
Cost Operator Builder
  │  Produces: Hamiltonian circuit or matrix
  ▼
Circuit Composer (QAOA / VQE / custom)
  │  Produces: parametric quantum circuit
  ▼
Execution Engine ─────────────────────────────────────────┐
  │                                                        │
  ├─ Ideal Simulator (statevector / density matrix)        │
  ├─ Noise Simulator (Kraus channels, depolarising, etc.)  │
  └─ QPU Adapter (IBM, IonQ, AWS Braket, etc.)             │
                                                           │
  ◄──────────────────────────────────────────────────────┘
  │  Produces: measurement samples (bitstrings + counts)
  ▼
Decoder
  │  Produces: candidate solutions in Problem IR variable space
  ▼
Verifier (independent; see VERIFICATION.md)
  │  Checks: constraint satisfaction, objective value
  ▼
Result with quality metrics and limitations
```

---

## Execution Modes

| Mode | Description | When to use |
|------|-------------|-------------|
| Ideal simulation | Exact statevector; no noise | Development, small circuits, unit tests |
| Noise simulation | Kraus channel model | Evaluating NISQ-era performance |
| QPU execution | Real hardware | Benchmarking, production (with cost guard) |

Each mode must be explicitly selected and recorded in the result metadata.
"We ran this on a QPU" must be verifiable from the result record.

---

## Terminology (enforced)

| Correct | Incorrect |
|---------|-----------|
| Quantum circuit simulation | Quantum computation |
| Measurement outcome | Quantum result |
| Amplitude of state \|x⟩ | Probability weight |
| QAOA ansatz | Quantum solution |
| Variational parameter | Quantum weight |
| Sampling from a distribution | Quantum inference |

---

## QPU Adapter Interface (planned)

```typescript
interface QPUAdapter {
  name: string;
  backend_id: string;
  max_qubits: number;
  supported_gates: string[];
  is_available(): Promise<boolean>;
  estimate_cost(circuit: QuantumCircuit): Promise<CostEstimate>;
  submit(circuit: QuantumCircuit, shots: number): Promise<JobHandle>;
  fetch_results(job: JobHandle): Promise<SampleResult>;
}
```

No QPU call is made without:
1. Cost estimate shown to user.
2. Explicit user approval.
3. Result recorded with backend name, job ID, and timestamp.

---

## What the Quantum Core is NOT

- Not a source of automatic speedup — speedup is a benchmark result.
- Not a metaphor engine — "superposition" means amplitude superposition.
- Not responsible for producing the final answer alone — the Verifier is independent.
- Not always the right tool — classical solvers are used when they are better.
