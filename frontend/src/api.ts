/**
 * YourQuantum — API Client
 * Typed wrappers around the FastAPI backend.
 * All inputs validated client-side before sending.
 */

const BASE_URL = '/api/v1'

export interface ComputeBudget {
  wall_time_seconds?: number
  memory_mb?: number
  quantum_shots?: number
}

export interface ProblemCreateRequest {
  description: string
  binary_variables: string[]
  objective_coefficients: Record<string, number>
  objective_direction: 'minimize' | 'maximize'
  equality_constraints: Array<{ lhs: Record<string, number>; rhs: number }>
  budget?: ComputeBudget
}

export interface ProblemResponse {
  problem_id: string
  description_formalised: string
  n_variables: number
  n_constraints: number
  n_objectives: number
  approved: boolean
  missing_blocking: number
  ir_summary: {
    variables: string[]
    objective_direction: string
    n_equality_constraints: number
  }
}

export interface JobCreateRequest {
  problem_id: string
  solver: 'cp_sat' | 'qaoa_aer'
  budget?: ComputeBudget
}

export interface JobStatus {
  job_id: string
  problem_id: string
  solver_name: string
  execution_status: 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'TIMED_OUT' | 'CANCELLED' | 'FAILED'
  math_status: string | null
  source: string | null
  publication_status?: string
  created_at: string
  started_at: string | null
  completed_at: string | null
  solve_time_seconds: number | null
  objective_value: number | null
  error_message: string | null
}

export interface CaseFact {
  id: string
  label: string
  value: unknown
  unit?: string | null
  source_text?: string | null
  confidence: number
}

export interface CaseOption {
  id: string
  title: string
  description: string
  pros: string[]
  cons: string[]
  attributes: Record<string, unknown>
}

export interface CaseCriterion {
  id: string
  name: string
  direction: 'maximize' | 'minimize'
  weight: number
  unit?: string | null
  is_mandatory: boolean
  threshold?: number | null
}

export interface CaseUnknown {
  id: string
  question: string
  impact_description: string
  default_assumption?: string | null
  answer?: string | null
  is_resolved: boolean
}

export interface CaseTradeoff {
  option_a_id: string
  option_b_id: string
  description: string
  gain: string
  sacrifice: string
}

export interface InputQuality {
  level: 'sufficient' | 'too_vague' | 'needs_options' | 'needs_numbers'
  reason: string
  suggestions: string[]
}

export interface DecisionCase {
  id: string
  title: string
  context: string
  status: 'intake' | 'clarification' | 'ready_for_modeling' | 'modeled' | 'evaluated'
  facts: CaseFact[]
  options: CaseOption[]
  criteria: CaseCriterion[]
  unknowns: CaseUnknown[]
  tradeoffs: CaseTradeoff[]
  priority_tokens?: string[]
  selected_priority_tokens?: string[]
  score_matrix?: Record<string, Record<string, ScoredValue>>
  break_even_point?: string | null
  input_quality?: InputQuality
  created_at: string
  updated_at: string
  problem_ir_id?: string | null
}

export interface ScoredValue {
  value: number
  unit?: string | null
  provenance: 'user_supplied' | 'derived' | 'assumed' | 'web_sourced' | 'llm_extracted'
  source_ref?: string | null
  confidence: number
}

export interface Evidence {
  id: string
  claim: string
  value: number | string | null
  unit?: string | null
  source_url: string
  source_title: string
  publisher?: string | null
  published_at?: string | null
  retrieved_at: string
  content_hash: string
  quote: string
  extraction_method: 'llm_extracted' | 'api_field' | 'table_cell' | 'user_verified'
  confidence: number
  conflicts_with: string[]
  target_param?: string | null
}

export interface EvidenceConflict {
  id: string
  target_param: string
  evidence_ids: string[]
  divergent_values: (number | string)[]
  spread_min?: number | null
  spread_max?: number | null
  resolution_method: string
  resolved_value?: number | string | null
  notes: string
}

export interface ConstraintResult {
  constraint_id: string
  satisfied: boolean
  hard: boolean
  violation_magnitude: number | null
  note: string | null
}

export interface RobustnessShockLevel {
  shock_percent: number
  retained_feasibility: boolean
  objective_value: number | null
  objective_change_percent: number
  max_residual: number
}

export interface RobustnessReport {
  candidate_id: string
  robustness_score: number
  verdict: 'HIGHLY_ROBUST' | 'MODERATELY_ROBUST' | 'FRAGILE'
  stress_test_survived_pct: number
  elasticity: number
  shock_levels: RobustnessShockLevel[]
  summary_pl: string
}

export interface VerificationReport {
  verdict: 'PASS' | 'FAIL' | 'PARTIAL' | 'UNKNOWN'
  verdict_reason: string
  feasible: boolean
  objective_value: number | null
  objective_recomputed: boolean
  solver_claimed_objective: number | null
  constraint_results: ConstraintResult[]
  domain_violations: string[]
  numerical_residual: number | null
  limitations: string[]
  sha256_hash?: string
  optimality_proven?: boolean
  dual_bound?: number | null
  optimality_gap_percent?: number | null
  robustness?: RobustnessReport | null
}

export interface QAOARunRecord {
  run_id: string
  problem_id: string
  encoding_id: string
  backend_name: string
  execution_mode: string
  n_qubits: number
  p_layers: number
  circuit_depth: number | null
  circuit_gate_count: number | null
  shots: number
  seed: number
  n_evaluations: number
  final_params: number[]
  final_energy: number | null
  converged: boolean
  optimiser: string
  sample_distribution: Record<string, number>
  top_k_bitstrings: string[]
  top_k_energies: number[]
  compile_time_seconds: number
  optimise_time_seconds: number
  sample_time_seconds: number
  total_time_seconds: number
  amplification_factor?: number | null
  ground_state_prob?: number | null
  random_guess_prob?: number | null
  two_qubit_gate_count?: number
  single_qubit_gate_count?: number
  multi_start_attempts?: number
  notes: string[]
}

export interface ProblemPreset {
  id: string
  title: string
  category: string
  description: string
  human_explanation: string
  human_rules: string[]
  variable_labels: Record<string, string>
  binary_variables: string[]
  objective_coefficients: Record<string, number>
  objective_direction: 'minimize' | 'maximize'
  equality_constraints: Array<{ lhs: Record<string, number>; rhs: number }>
  time_limit: number
  shots: number
  recommended_solver: 'cp_sat' | 'qaoa_aer'
  quantum_ready: boolean
  tags: string[]
  image_slug: string
}

export interface FormalizeResponse {
  description_raw: string
  description_formalised: string
  binary_variables: string[]
  objective_direction: 'minimize' | 'maximize'
  objective_coefficients: Record<string, number>
  equality_constraints: Array<{ lhs: Record<string, number>; rhs: number }>
  inequality_constraints: Array<{ lhs: Record<string, number>; rhs: number }>
  assumptions: string[]
  missing_information: string[]
  identified_archetype: string
  break_even_point?: string | null
}

export interface BenchmarkResponse {
  problem_id: string
  cp_sat_job_id: string
  qaoa_job_id: string
  status: string
}

export interface JobResult {
  job_id: string
  problem_id: string
  execution_status: string
  math_status: string | null
  source: string | null
  publication_status?: string
  is_verified_recommendation?: boolean
  objective_value: number | null
  solve_time_seconds: number | null
  solver_result: {
    assignment?: Record<string, number>
    metadata?: {
      qaoa_run_record?: QAOARunRecord
    }
  } | null
  verification: VerificationReport | null
  error_message: string | null
}

async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const resp = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!resp.ok) {
    const text = await resp.text()
    throw new Error(`API ${resp.status}: ${text}`)
  }
  return resp.json() as Promise<T>
}

export const api = {
  createProblem: (req: ProblemCreateRequest & { approved?: boolean }) =>
    request<ProblemResponse>('/problems', {
      method: 'POST',
      body: JSON.stringify(req),
    }),

  approveProblem: (id: string) =>
    request<ProblemResponse>(`/problems/${id}/approve`, {
      method: 'POST',
    }),

  getProblem: (id: string) =>
    request<Record<string, unknown>>(`/problems/${id}`),

  createJob: (req: JobCreateRequest) =>
    request<{ job_id: string; status: string }>('/jobs', {
      method: 'POST',
      body: JSON.stringify(req),
    }),

  getJobStatus: (id: string) =>
    request<JobStatus>(`/jobs/${id}`),

  getJobResult: (id: string) =>
    request<JobResult>(`/jobs/${id}/result`),

  getSolvers: () =>
    request<{ solvers: Array<{ name: string; version: string }> }>(
      '/health/solvers',
    ),

  getPresets: () =>
    request<ProblemPreset[]>('/presets'),

  formalizeProblem: (text: string) =>
    request<FormalizeResponse>('/problems/formalize', {
      method: 'POST',
      body: JSON.stringify({ text }),
    }),

  formalizeCase: (caseData: DecisionCase) =>
    request<FormalizeResponse>('/cases/formalize', {
      method: 'POST',
      body: JSON.stringify(caseData),
    }),

  analyzeCase: (text: string) =>
    request<DecisionCase>('/cases/analyze', {
      method: 'POST',
      body: JSON.stringify({ text }),
    }),

  saveCase: (caseData: DecisionCase) =>
    request<DecisionCase>('/cases', {
      method: 'POST',
      body: JSON.stringify(caseData),
    }),

  getCase: (id: string) =>
    request<DecisionCase>(`/cases/${id}`),

  createBenchmark: (req: { problem_id: string; budget?: ComputeBudget }) =>
    request<BenchmarkResponse>('/benchmarks', {
      method: 'POST',
      body: JSON.stringify(req),
    }),

  getHelpKnowledge: () =>
    request<HelpResponse>('/help'),

  getEngineSnapshot: () =>
    request<EngineCapabilitySnapshot>('/help/snapshot'),

  verifyApiAccess: (password: string) =>
    request<{ valid: boolean; token: string; message: string }>('/auth/verify-api-access', {
      method: 'POST',
      body: JSON.stringify({ password }),
    }),

  runUniversalCompute: (req: UniversalComputeRequest, keyOrToken: string) =>
    request<UniversalComputeResponse>('/universal/compute', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${keyOrToken}`,
        'X-API-Key': keyOrToken,
      },
      body: JSON.stringify(req),
    }),

  getSdkDownloadUrl: (sdkType: 'python' | 'typescript', key: string) =>
    `${BASE_URL}/sdk/download?sdk_type=${sdkType}&key=${encodeURIComponent(key)}`,
}

export interface UniversalVariableItem {
  id: string
  name: string
  cost?: number
  value?: number
  attributes?: Record<string, unknown>
}

export interface UniversalConstraintItem {
  id?: string
  name?: string
  type: 'budget' | 'cardinality_exact' | 'cardinality_max' | 'cardinality_min' | 'incompatible' | 'dependency' | 'linear'
  attribute?: string
  limit?: number
  count?: number
  var_ids?: string[]
  linear_lhs?: Record<string, number>
  linear_op?: '<=' | '>=' | '=='
  linear_rhs?: number
}

export interface UniversalComputeRequest {
  domain?: string
  title: string
  variables: UniversalVariableItem[]
  objective_direction?: 'maximize' | 'minimize'
  objective_attribute?: string
  objective_coefficients?: Record<string, number>
  constraints?: UniversalConstraintItem[]
  solver?: 'auto' | 'hybrid_benders' | 'qaoa' | 'cpsat'
  include_stress_test?: boolean
}

export interface UniversalComputeResponse {
  status: 'SUCCESS' | 'INFEASIBLE' | 'ERROR'
  title: string
  domain: string
  solver_used: string
  compute_time_ms: number
  optimal_assignment: Record<string, number>
  optimal_selection: Array<{
    id: string
    name: string
    cost?: number
    value?: number
    attributes?: Record<string, unknown>
  }>
  total_objective_value: number
  dual_bound: number | null
  optimality_gap_percent: number | null
  optimality_proven: boolean
  sha256_passport: string
  verification: {
    feasible: boolean
    verdict: string
    residual: number
  }
  sensitivity_report?: {
    robustness_score: number
    verdict: string
    summary_pl: string
  }
}

export interface HelpTopic {
  id: string
  title: string
  short_desc: string
  category: string
  content_markdown: string
  read_time_minutes: number
  badge?: string
  target_stages: string[]
}

export interface EngineCapabilitySnapshot {
  engine_version: string
  active_solvers_count: number
  solvers: Array<{ name: string; version: string; kind: string; status: string }>
  supported_dilemma_types: string[]
  verification_mode: string
  last_updated: string
}

export interface HelpResponse {
  engine_status: EngineCapabilitySnapshot
  categories: string[]
  topics: HelpTopic[]
  faq: Array<{ q: string; a: string }>
  glossary: Array<{ term: string; meaning: string }>
}

export async function researchEvidence(params: {
  case_id?: string
  target_parameters?: Array<{ param_id: string; query_text: string; expected_unit?: string; rationale?: string }>
  max_results_per_param?: number
}): Promise<{
  status: string
  evidence_count: number
  conflict_count: number
  evidence: Evidence[]
  conflicts: EvidenceConflict[]
  port_status: Record<string, unknown>
}> {
  const res = await fetch(`${BASE_URL}/evidence/research`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  })
  if (!res.ok) {
    throw new Error(`Błąd badania źródeł: ${res.statusText}`)
  }
  return res.json()
}

export async function getEvidenceRecord(id: string): Promise<Evidence> {
  const res = await fetch(`${BASE_URL}/evidence/${id}`)
  if (!res.ok) {
    throw new Error(`Nie znaleziono rekordu dowodu: ${id}`)
  }
  return res.json()
}
