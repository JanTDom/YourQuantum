"""
YourQuantum — Problem Intermediate Representation
Versioned, domain-agnostic, immutable once approved.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class SolveMode(str, Enum):
    SOLVE = "solve"
    OPTIMIZE = "optimize"
    VERIFY = "verify"
    ANALYZE = "analyze"


class VariableDomain(str, Enum):
    BINARY = "binary"
    INTEGER = "integer"
    CONTINUOUS = "continuous"
    CATEGORICAL = "categorical"
    SET = "set"


class ConstraintType(str, Enum):
    EQUALITY = "equality"
    INEQUALITY_LE = "inequality_le"   # lhs <= rhs
    INEQUALITY_GE = "inequality_ge"   # lhs >= rhs
    LOGICAL = "logical"
    CARDINALITY = "cardinality"
    DOMAIN = "domain"


class ObjectiveDirection(str, Enum):
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"


class Provenance(str, Enum):
    USER_SUPPLIED = "user_supplied"
    DERIVED = "derived"
    ASSUMED = "assumed"
    WEB_SOURCED = "web_sourced"
    LLM_EXTRACTED = "llm_extracted"


class MissingInfoImpact(str, Enum):
    BLOCKS_SOLVING = "blocks_solving"
    REDUCES_QUALITY = "reduces_quality"
    MINOR = "minor"


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class Variable(BaseModel):
    id: str
    name: str
    domain: VariableDomain
    lower_bound: float | None = None
    upper_bound: float | None = None
    allowed_values: list[Any] | None = None   # for CATEGORICAL / SET
    unit: str | None = None
    provenance: Provenance = Provenance.USER_SUPPLIED
    description: str | None = None


class DataSource(BaseModel):
    id: str
    name: str
    content_hash: str | None = None       # SHA-256 of raw data
    imported_at: datetime | None = None
    source_description: str | None = None  # filename, URL, etc.
    version: int = 1


class Constraint(BaseModel):
    id: str
    type: ConstraintType
    # Expression stored as a safe expression tree reference (string ID)
    lhs_expression_id: str
    rhs_expression_id: str | None = None  # None for DOMAIN or LOGICAL
    hard: bool = True                      # False = soft (penalised)
    penalty_weight: float | None = None
    source: str | None = None             # which user statement / data field
    description: str | None = None


class Objective(BaseModel):
    id: str
    direction: ObjectiveDirection
    expression_id: str
    priority: int = 1                      # 1 = primary
    description: str | None = None


class Assumption(BaseModel):
    id: str
    statement: str
    confidence: Literal["high", "medium", "low"] = "medium"
    source: Provenance = Provenance.USER_SUPPLIED


class MissingInfo(BaseModel):
    id: str
    description: str
    impact: MissingInfoImpact
    clarification_question: str
    resolved: bool = False
    resolution: str | None = None


# ---------------------------------------------------------------------------
# Expression Tree Node (safe — no eval/exec)
# ---------------------------------------------------------------------------

class ExprNode(BaseModel):
    """
    A single node in a safe expression tree.
    All arithmetic is evaluated by our own evaluator, never via eval/exec.
    """
    id: str
    op: Literal[
        "const", "var",
        "add", "sub", "mul", "div",
        "min", "max", "sum", "neg",
        "eq", "le", "ge", "lt", "gt", "ne",
        "and_", "or_", "not_",
        "if_",
    ]
    value: float | int | str | None = None    # for "const" and "var" (var id)
    children: list[str] = Field(default_factory=list)  # child node IDs


class ExpressionRegistry(BaseModel):
    """Flat registry of all expression nodes for this problem."""
    nodes: dict[str, ExprNode] = Field(default_factory=dict)

    def add(self, node: ExprNode) -> str:
        self.nodes[node.id] = node
        return node.id

    def const(self, value: float | int) -> str:
        nid = f"const_{uuid.uuid4().hex[:8]}"
        return self.add(ExprNode(id=nid, op="const", value=value))

    def var(self, variable_id: str) -> str:
        nid = f"var_{variable_id}"
        return self.add(ExprNode(id=nid, op="var", value=variable_id))


# ---------------------------------------------------------------------------
# Budget
# ---------------------------------------------------------------------------

class ComputeBudget(BaseModel):
    wall_time_seconds: float = Field(default=30.0, gt=0.0, le=600.0)
    memory_mb: float = Field(default=512.0, gt=0.0, le=4096.0)
    max_iterations: int | None = Field(default=None, gt=0, le=100000)
    cost_usd: float | None = Field(default=None, ge=0.0, le=1000.0)
    quantum_shots: int = Field(default=1024, gt=0, le=10000)


# ---------------------------------------------------------------------------
# ProblemIR — the canonical versioned contract
# ---------------------------------------------------------------------------

class ProblemIR(BaseModel):
    schema_version: str = "0.2"
    problem_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_problem_id: str | None = None
    version: int = 1

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    description_raw: str
    description_formalised: str

    mode: SolveMode = SolveMode.OPTIMIZE

    variables: list[Variable] = Field(default_factory=list)
    data_sources: list[DataSource] = Field(default_factory=list)
    expressions: ExpressionRegistry = Field(default_factory=ExpressionRegistry)
    constraints: list[Constraint] = Field(default_factory=list)
    objectives: list[Objective] = Field(default_factory=list)
    assumptions: list[Assumption] = Field(default_factory=list)
    missing_information: list[MissingInfo] = Field(default_factory=list)

    budget: ComputeBudget = Field(default_factory=ComputeBudget)

    # Approval state
    approved: bool = False
    approved_at: datetime | None = None

    @model_validator(mode="after")
    def _check_objectives_for_optimize(self) -> "ProblemIR":
        if self.mode == SolveMode.OPTIMIZE and self.approved:
            if not self.objectives:
                raise ValueError(
                    "An approved OPTIMIZE problem must have at least one objective."
                )
        return self

    @property
    def blocking_missing_info(self) -> list[MissingInfo]:
        return [
            m for m in self.missing_information
            if m.impact == MissingInfoImpact.BLOCKS_SOLVING and not m.resolved
        ]

    @property
    def is_ready_to_solve(self) -> bool:
        return self.approved and len(self.blocking_missing_info) == 0

    def variable_by_id(self, vid: str) -> Variable | None:
        return next((v for v in self.variables if v.id == vid), None)


# ---------------------------------------------------------------------------
# ProblemSpec — user-facing input (before formalisation)
# ---------------------------------------------------------------------------

class ProblemSpec(BaseModel):
    """Raw user input — converted to ProblemIR by the formaliser."""
    description: str = Field(min_length=10)
    data_json: dict[str, Any] | None = None
    constraints_text: list[str] = Field(default_factory=list)
    objective_text: str | None = None
    budget: ComputeBudget = Field(default_factory=ComputeBudget)


