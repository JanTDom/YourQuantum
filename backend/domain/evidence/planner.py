"""
YourQuantum — Evidence Research Planner (Phase C3 & C4)
Orchestrates privacy-preserving research queries for missing parameter data,
coordinates document fetching and extraction, verifies quotes, and detects conflicts.
"""
from __future__ import annotations

import logging
import statistics
import uuid
from typing import Any

from backend.domain.decision_case import DecisionCase, ScoredValue
from backend.domain.evidence.models import Evidence, EvidenceConflict, ResearchQuery
from backend.domain.evidence.ports import EvidenceSourcePort
from backend.domain.problem_ir import DataSource, ProblemIR, Provenance
from backend.infrastructure.web_research.extractor import EvidenceExtractor

logger = logging.getLogger(__name__)


class ResearchPlanner:
    """
    Identifies missing parameter data in decision models, formulates privacy-preserving queries,
    and coordinates evidence collection with strict conflict handling.
    """

    def __init__(
        self,
        evidence_port: EvidenceSourcePort | None = None,
        extractor: EvidenceExtractor | None = None,
    ) -> None:
        if evidence_port is None:
            from backend.infrastructure.web_research.search_adapter import WebResearchAdapter
            evidence_port = WebResearchAdapter(api_key=None)
        self.port = evidence_port

        self.extractor = extractor or EvidenceExtractor()


    def identify_missing_parameters(self, case: DecisionCase) -> list[ResearchQuery]:
        """
        Scan DecisionCase score_matrix for cells lacking verified source references.
        Generates targeted, privacy-preserving research queries without leaking user private context.
        """
        queries: list[ResearchQuery] = []

        for opt in case.options:
            for crit in case.criteria:
                cell: ScoredValue | None = case.score_matrix.get(opt.id, {}).get(crit.id)
                needs_evidence = False

                if cell is None:
                    needs_evidence = True
                elif cell.source_ref is None or not str(cell.source_ref).strip():
                    needs_evidence = True
                elif cell.provenance in (Provenance.ASSUMED, Provenance.LLM_EXTRACTED):
                    needs_evidence = True

                if needs_evidence:
                    param_id = f"{opt.id}.{crit.id}"
                    # Create targeted privacy-preserving search query
                    opt_label = opt.title or opt.id
                    crit_label = crit.name or crit.id
                    query_text = f"{opt_label} {crit_label}"
                    if crit.unit:
                        query_text += f" {crit.unit}"

                    queries.append(
                        ResearchQuery(
                            id=f"rq_{uuid.uuid4().hex[:8]}",
                            target_param=param_id,
                            query_text=query_text,
                            expected_unit=crit.unit,
                            rationale=f"Fetch empirical evidence for option '{opt_label}' on criterion '{crit_label}'",
                        )
                    )

        return queries

    async def execute_research_plan(
        self,
        queries: list[ResearchQuery],
        max_results_per_query: int = 2,
    ) -> tuple[list[Evidence], list[EvidenceConflict]]:
        """
        Execute the research plan: query -> fetch -> extract with quote verification -> conflict detection.
        """
        collected_evidence: list[Evidence] = []
        evidence_by_param: dict[str, list[Evidence]] = {}

        if not self.port.is_available():
            logger.info("Evidence source port is offline or unconfigured. Skipping live research.")
            return [], []

        for q in queries:
            search_results = await self.port.search(q.query_text, max_results=max_results_per_query)
            for res in search_results:
                doc = await self.port.fetch_document(res.url)
                if not doc:
                    continue

                evidence = await self.extractor.extract_parameter_evidence(
                    document=doc,
                    target_param=q.target_param,
                    expected_unit=q.expected_unit,
                    parameter_description=q.rationale,
                )

                if evidence and evidence.value is not None:
                    collected_evidence.append(evidence)
                    if q.target_param not in evidence_by_param:
                        evidence_by_param[q.target_param] = []
                    evidence_by_param[q.target_param].append(evidence)

        # Detect conflicts across multiple sources for the same parameter
        conflicts: list[EvidenceConflict] = []
        for param_id, ev_list in evidence_by_param.items():
            if len(ev_list) > 1:
                conflict = self._detect_conflict(param_id, ev_list)
                if conflict:
                    conflicts.append(conflict)

        return collected_evidence, conflicts

    def _detect_conflict(self, param_id: str, ev_list: list[Evidence]) -> EvidenceConflict | None:
        """Checks if multiple pieces of evidence report divergent values."""
        values = [e.value for e in ev_list if e.value is not None]
        if len(values) < 2:
            return None

        # Check for numeric divergence
        numeric_values: list[float] = []
        is_all_numeric = True
        for v in values:
            try:
                numeric_values.append(float(v))
            except (ValueError, TypeError):
                is_all_numeric = False
                break

        has_divergence = False
        spread_min: float | None = None
        spread_max: float | None = None
        resolved_val: float | str | None = None

        if is_all_numeric:
            spread_min = min(numeric_values)
            spread_max = max(numeric_values)
            if abs(spread_max - spread_min) > 1e-4:
                has_divergence = True
                resolved_val = float(statistics.median(numeric_values))
        else:
            # String comparison
            str_values = [str(v).strip().lower() for v in values]
            if len(set(str_values)) > 1:
                has_divergence = True
                resolved_val = values[0]

        if has_divergence:
            ev_ids = [e.id for e in ev_list]
            # Cross-reference conflicts
            for e in ev_list:
                e.conflicts_with = [other_id for other_id in ev_ids if other_id != e.id]

            return EvidenceConflict(
                id=f"conf_{uuid.uuid4().hex[:8]}",
                target_param=param_id,
                evidence_ids=ev_ids,
                divergent_values=values,
                spread_min=spread_min,
                spread_max=spread_max,
                resolution_method="median" if is_all_numeric else "unresolved",
                resolved_value=resolved_val,
                notes=f"Conflicting values across {len(ev_list)} web sources. Median candidate computed.",
            )

        return None

    def apply_evidence_to_case(
        self,
        case: DecisionCase,
        evidence_list: list[Evidence],
        conflicts: list[EvidenceConflict] | None = None,
    ) -> DecisionCase:
        """
        Update DecisionCase score_matrix with web-sourced evidence and provenance tags.
        """
        conflicts_by_param = {c.target_param: c for c in (conflicts or [])}
        evidence_by_param: dict[str, Evidence] = {}

        for ev in evidence_list:
            if ev.target_param and ev.target_param not in evidence_by_param:
                evidence_by_param[ev.target_param] = ev

        for opt in case.options:
            if opt.id not in case.score_matrix:
                case.score_matrix[opt.id] = {}

            for crit in case.criteria:
                param_id = f"{opt.id}.{crit.id}"

                # Check if conflict exists
                if param_id in conflicts_by_param:
                    conf = conflicts_by_param[param_id]
                    if conf.resolved_value is not None:
                        # Median value with explicit marking
                        case.score_matrix[opt.id][crit.id] = ScoredValue(
                            value=conf.resolved_value,
                            unit=crit.unit,
                            provenance=Provenance.WEB_SOURCED,
                            source_ref=f"conflict_median({','.join(conf.evidence_ids)})",
                            confidence=0.7,
                        )
                elif param_id in evidence_by_param:
                    ev = evidence_by_param[param_id]
                    case.score_matrix[opt.id][crit.id] = ScoredValue(
                        value=ev.value,
                        unit=ev.unit or crit.unit,
                        provenance=Provenance.WEB_SOURCED,
                        source_ref=ev.id,
                        confidence=ev.confidence,
                    )

        return case

    def attach_evidence_to_ir(
        self,
        problem: ProblemIR,
        evidence_list: list[Evidence],
    ) -> ProblemIR:
        """
        Populates problem.data_sources with one DataSource per unique web source.
        Attaches evidence provenance to matching variables.
        """
        existing_sources = {ds.content_hash: ds for ds in problem.data_sources if ds.content_hash}

        for ev in evidence_list:
            if ev.content_hash not in existing_sources:
                ds = DataSource(
                    id=f"ds_{ev.id}",
                    name=ev.source_title or ev.publisher or "Web Document",
                    content_hash=ev.content_hash,
                    source_description=ev.source_url,
                    version=1,
                )
                problem.data_sources.append(ds)
                existing_sources[ev.content_hash] = ds

            # Link to variables if target_param matches variable id
            if ev.target_param:
                for v in problem.variables:
                    if v.id == ev.target_param:
                        v.provenance = Provenance.WEB_SOURCED
                        if ev.unit and not v.unit:
                            v.unit = ev.unit

        return problem
