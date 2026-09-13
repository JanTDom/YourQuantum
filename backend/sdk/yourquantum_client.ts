/**
 * YourQuantum Official TypeScript SDK (Zero-Dependency)
 * Universal Multi-Domain Quantum & Classical Decision Optimization Client.
 * 
 * Works in Browser and Node.js 18+ environments.
 * 
 * Usage:
 *   import { YourQuantumClient } from './yourquantum_client';
 * 
 *   const client = new YourQuantumClient({ apiKey: 'YOUR_API_TOKEN' });
 *   const result = await client.solvePortfolio({
 *     projects: [
 *       { id: 'dev_1', name: 'Nowy silnik rekomendacji', cost: 120000, value: 380000 },
 *       { id: 'dev_2', name: 'Refaktoryzacja baz danych', cost: 45000, value: 160000 },
 *       { id: 'dev_3', name: 'Aplikacja mobilna iOS', cost: 95000, value: 240000 },
 *     ],
 *     budgetLimit: 170000,
 *   });
 *   console.log('Optymalna alokacja:', result.optimal_selection);
 *   console.log('Paszport SHA-256:', result.sha256_passport);
 */

export interface VariableItem {
  id: string;
  name: string;
  cost?: number;
  value?: number;
  attributes?: Record<string, number | string | boolean>;
  [key: string]: unknown;
}

export interface ConstraintItem {
  id?: string;
  name?: string;
  type: 'budget' | 'cardinality_exact' | 'cardinality_max' | 'cardinality_min' | 'incompatible' | 'dependency' | 'linear';
  attribute?: string;
  limit?: number;
  count?: number;
  var_ids?: string[];
  linear_lhs?: Record<string, number>;
  linear_op?: '<=' | '>=' | '==';
  linear_rhs?: number;
}

export interface UniversalComputeRequest {
  domain?: 'general' | 'finance' | 'logistics' | 'hr' | 'portfolio' | string;
  title: string;
  variables: VariableItem[];
  objective_direction?: 'maximize' | 'minimize';
  objective_attribute?: string;
  objective_coefficients?: Record<string, number>;
  constraints?: ConstraintItem[];
  solver?: 'auto' | 'hybrid_benders' | 'qaoa' | 'cpsat';
  include_stress_test?: boolean;
}

export interface UniversalComputeResponse {
  status: 'SUCCESS' | 'INFEASIBLE' | 'ERROR';
  title: string;
  domain: string;
  solver_used: string;
  compute_time_ms: number;
  optimal_assignment: Record<string, number>;
  optimal_selection: VariableItem[];
  total_objective_value: number;
  dual_bound: number | null;
  optimality_gap_percent: number | null;
  optimality_proven: boolean;
  sha256_passport: string;
  verification: {
    feasible: boolean;
    verdict: string;
    residual: number;
  };
  sensitivity_report?: {
    robustness_score: number;
    verdict: string;
    summary_pl: string;
  };
}

export class YourQuantumClient {
  private readonly apiKey: string;
  private readonly baseUrl: string;

  constructor(options: { apiKey?: string; baseUrl?: string } = {}) {
    this.apiKey = (options.apiKey || '').trim();
    this.baseUrl = (options.baseUrl || 'https://yourquantum.pl').replace(/\/+$/, '');
  }

  public async solve(request: UniversalComputeRequest): Promise<UniversalComputeResponse> {
    const url = `${this.baseUrl}/api/v1/universal/compute`;
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.apiKey}`,
        'X-API-Key': this.apiKey,
        'User-Agent': 'YourQuantum-TS-SDK/1.0.0',
      },
      body: JSON.stringify({
        domain: request.domain || 'general',
        title: request.title,
        variables: request.variables,
        constraints: request.constraints || [],
        objective_direction: request.objective_direction || 'maximize',
        objective_attribute: request.objective_attribute || 'value',
        objective_coefficients: request.objective_coefficients || {},
        solver: request.solver || 'auto',
        include_stress_test: request.include_stress_test ?? true,
      }),
    });

    if (!res.ok) {
      const errText = await res.text();
      let errorDetail = errText;
      try {
        const parsed = JSON.parse(errText);
        errorDetail = parsed.detail || errText;
      } catch {
        // use raw text
      }
      throw new Error(`YourQuantum API error [HTTP ${res.status}]: ${errorDetail}`);
    }

    return (await res.json()) as UniversalComputeResponse;
  }

  /**
   * Kognitywna formalizacja problemu decyzyjnego w architekturze inspirowanej ludzkim mózgiem
   * (Prefrontal Working Memory, Episodic Hippocampus, Active Inference).
   */
  public async cognitiveIntake(params: {
    query: string;
    sessionId?: string;
  }): Promise<Record<string, any>> {
    const url = `${this.baseUrl}/api/v1/cognitive/intake`;
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.apiKey}`,
        'X-API-Key': this.apiKey,
        'User-Agent': 'YourQuantum-TS-SDK/1.0.0',
      },
      body: JSON.stringify({
        query: params.query,
        session_id: params.sessionId,
      }),
    });
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`YourQuantum Cognitive API error [HTTP ${res.status}]: ${errText}`);
    }
    return (await res.json()) as Record<string, any>;
  }

  /**
   * Szybka optymalizacja portfela inwestycji / budżetu.
   */
  public async solvePortfolio(params: {
    projects: VariableItem[];
    budgetLimit: number;
    budgetAttribute?: string;
    objectiveAttribute?: string;
    solver?: 'auto' | 'hybrid_benders' | 'qaoa' | 'cpsat';
  }): Promise<UniversalComputeResponse> {
    return this.solve({
      domain: 'finance',
      title: 'Optymalizacja Portfela Projektów',
      variables: params.projects,
      constraints: [
        {
          name: 'Limit budżetowy kapitału',
          type: 'budget',
          attribute: params.budgetAttribute || 'cost',
          limit: params.budgetLimit,
        },
      ],
      objective_direction: 'maximize',
      objective_attribute: params.objectiveAttribute || 'value',
      solver: params.solver || 'auto',
    });
  }

  /**
   * Wybór optymalnego podzbioru K elementów z ograniczeniami wzajemnych wykluczeń.
   */
  public async solveSelection(params: {
    options: VariableItem[];
    k: number;
    incompatiblePairs?: [string, string][];
    objectiveAttribute?: string;
    solver?: 'auto' | 'hybrid_benders' | 'qaoa' | 'cpsat';
  }): Promise<UniversalComputeResponse> {
    const constraints: ConstraintItem[] = [
      {
        name: `Wybór dokładnie ${params.k} elementów`,
        type: 'cardinality_exact',
        count: params.k,
      },
    ];

    if (params.incompatiblePairs) {
      for (const [a, b] of params.incompatiblePairs) {
        constraints.push({
          name: `Wykluczenie ${a} z ${b}`,
          type: 'incompatible',
          var_ids: [a, b],
        });
      }
    }

    return this.solve({
      domain: 'general',
      title: `Wybór ${params.k} wariantów`,
      variables: params.options,
      constraints,
      objective_direction: 'maximize',
      objective_attribute: params.objectiveAttribute || 'value',
      solver: params.solver || 'auto',
    });
  }
}
