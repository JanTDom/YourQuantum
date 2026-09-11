---
name: yq-quantum-core
description: >-
  Use this skill when implementing or extending the quantum algorithm module:
  QUBO/Ising encoding, cost Hamiltonian construction, QAOA/VQE circuit design,
  ideal or noise-model simulation, measurement sampling, variational parameter
  optimisation, or QPU backend integration. Activate when working on any
  component of the quantum execution path described in docs/QUANTUM_CORE.md.
  This skill requires strict encoding verification and full accounting of
  computational cost.
---

# yq-quantum-core — Quantum Algorithm Module

## Input

- An approved, versioned Problem IR.
- Target execution mode: ideal simulation / noise simulation / QPU.
- Compute budget: time, shots (for sampling), cost (for QPU).

## Procedure

### 1. Read Quantum Core Design

Read `docs/QUANTUM_CORE.md` in full before writing any code.

### 2. Verify Encoding Correctness

Before running any circuit:

**QUBO encoding check:**
- Every binary variable x_i ∈ {0, 1} is mapped to a qubit.
- The QUBO objective Q is symmetric (Q = Qᵀ).
- The ground state of the QUBO corresponds to the optimal solution.
- Verify with a small brute-force check on ≤ 10 variables if possible.

**Ising encoding check:**
- h_i and J_ij derived correctly from Q.
- Verify: E_Ising(s) = E_QUBO(x) under the mapping x_i = (1 - s_i) / 2.

Document the encoding scheme used and any approximations in the result metadata.

### 3. Circuit Construction

- Use established ansätze (QAOA, VQE hardware-efficient) unless there is a
  specific reason to deviate; document the reason.
- Verify gate count, qubit count, and circuit depth before submitting.
- Confirm the target backend supports all gates in the circuit.

### 4. Select Execution Mode

| Mode | When to use | Cost |
|------|-------------|------|
| Ideal statevector | Development, small circuits (≤ 20 qubits), unit tests | Free |
| Noise simulation | Evaluating NISQ-era fidelity | Free |
| QPU | Benchmarking, production (with user approval) | Paid |

The execution mode MUST be recorded in the result metadata. Never mix modes
within a single benchmark comparison.

### 5. QPU Calls (if applicable)

Before any QPU call:
1. Estimate cost using `adapter.estimate_cost(circuit)`.
2. Show cost estimate to user.
3. Receive explicit user approval.
4. Record: backend name, job ID, qubit count, shot count, timestamp.

### 6. Sampling and Decoding

- Run with the configured shot count.
- Record the full measurement distribution (bitstring → count).
- Decode the top-k bitstrings back to Problem IR variable space.
- Pass all decoded candidates to the Verifier.

### 7. Variational Optimisation (QAOA/VQE)

- Run the classical optimiser loop (COBYLA, SPSA, or Adam).
- Record: number of iterations, final parameters, convergence status.
- Do NOT stop at the first iteration and report it as converged.
- If the optimiser did not converge, report `status: "not_converged"`.

### 8. Terminology Enforcement (non-negotiable)

Do NOT use these terms in code comments, logs, or user-facing text:

| Forbidden (in quantum context) | Correct alternative |
|-------------------------------|---------------------|
| "quantum result" (for simulation output) | "simulation output" |
| "superposition of candidates" | "amplitude distribution" |
| "quantum inference" | "sampling from a measured distribution" |
| "quantum annealing" (for simulated annealing) | "simulated annealing" |
| "quantum weight" | "variational parameter" |

### 9. Update Capabilities

Update `docs/CAPABILITIES.md` status for each implemented capability.

## Required Output

- Implemented and tested component(s) of the quantum execution path.
- Verified encoding (with brute-force check or formal proof for small cases).
- Result record including execution mode, qubit/shot counts, and limitations.
- Updated `docs/CAPABILITIES.md`.

## Abort Conditions

- If qubit count exceeds available simulator capacity, reduce problem size or
  switch to a compatible backend. Do NOT silently truncate the problem.
- If a QPU backend is unavailable and QPU mode was selected, return an error;
  do not fall back silently to simulation without telling the user.
- If the encoding cannot be verified, halt and report the verification failure.

## What This Skill Does NOT Do

- Does not claim simulation results are equivalent to QPU results.
- Does not promise quantum advantage — that is measured by yq-benchmark.
- Does not skip encoding verification to save time.
- Does not present approximate solutions as exact optima.
