"""
YourQuantum Official Python SDK (Zero-Dependency)
Universal Multi-Domain Quantum & Classical Decision Optimization Client.

Usage:
    from yourquantum_sdk import YourQuantumClient

    client = YourQuantumClient(api_key="YOUR_API_TOKEN", base_url="https://yourquantum.pl")
    
    # Example 1: Multi-Project Capital Allocation
    result = client.solve_portfolio(
        projects=[
            {"id": "p1", "name": "Nowa linia produkcyjna", "cost": 150000, "expected_roi": 420000},
            {"id": "p2", "name": "Ekspansja magazynowa", "cost": 90000, "expected_roi": 230000},
            {"id": "p3", "name": "Automatyzacja AI", "cost": 60000, "expected_roi": 195000},
            {"id": "p4", "name": "Flota elektryczna", "cost": 120000, "expected_roi": 180000},
        ],
        budget_limit=220000,
        budget_attribute="cost",
        objective_attribute="expected_roi",
    )
    print("Wybrane projekty:", result["optimal_selection"])
    print("Paszport SHA-256:", result["sha256_passport"])
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Union


class YourQuantumError(Exception):
    """Base exception for YourQuantum SDK errors."""
    pass


class YourQuantumClient:
    """Universal client for YourQuantum Multi-Domain Optimization API."""

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://yourquantum.pl",
        timeout: float = 30.0,
    ):
        self.api_key = (api_key or os.getenv("YQ_API_KEY", "")).strip()
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "X-API-Key": self.api_key,
            "User-Agent": "YourQuantum-Python-SDK/1.0.0",
        }

        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                res_data = response.read().decode("utf-8")
                return json.loads(res_data)
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8")
            try:
                parsed = json.loads(err_msg)
                detail = parsed.get("detail", err_msg)
            except Exception:
                detail = err_msg
            raise YourQuantumError(f"HTTP {e.code}: {detail}") from e
        except urllib.error.URLError as e:
            raise YourQuantumError(f"Połączenie nieudane: {e.reason}") from e

    def solve(
        self,
        title: str,
        variables: List[Dict[str, Any]],
        constraints: Optional[List[Dict[str, Any]]] = None,
        objective_direction: str = "maximize",
        objective_attribute: Optional[str] = "value",
        objective_coefficients: Optional[Dict[str, float]] = None,
        solver: str = "auto",
        domain: str = "general",
        include_stress_test: bool = True,
    ) -> Dict[str, Any]:
        """
        Uniwersalne rozwiązanie dowolnego wielozadaniowego problemu decyzyjnego.
        """
        payload = {
            "domain": domain,
            "title": title,
            "variables": variables,
            "constraints": constraints or [],
            "objective_direction": objective_direction,
            "objective_attribute": objective_attribute,
            "objective_coefficients": objective_coefficients or {},
            "solver": solver,
            "include_stress_test": include_stress_test,
        }
        return self._request("/api/v1/universal/compute", payload)

    # -----------------------------------------------------------------------
    # Wygodne metody pomocnicze dla popularnych dziedzin
    # -----------------------------------------------------------------------

    def solve_portfolio(
        self,
        projects: List[Dict[str, Any]],
        budget_limit: float,
        budget_attribute: str = "cost",
        objective_attribute: str = "value",
        solver: str = "auto",
    ) -> Dict[str, Any]:
        """
        Optymalizacja alokacji kapitału i portfela inwestycji.
        Wybiera podzbiór projektów maksymalizujący zwrot bez przekroczenia budżetu.
        """
        constraints = [
            {
                "name": "Limit budżetowy",
                "type": "budget",
                "attribute": budget_attribute,
                "limit": budget_limit,
            }
        ]
        return self.solve(
            title="Optymalizacja Portfela Projektów",
            domain="finance",
            variables=projects,
            constraints=constraints,
            objective_direction="maximize",
            objective_attribute=objective_attribute,
            solver=solver,
        )

    def cognitive_intake(
        self,
        query: str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Kognitywna formalizacja problemu decyzyjnego w architekturze inspirowanej ludzkim mózgiem
        (Prefrontal Working Memory, Episodic Hippocampus, Active Inference).
        """
        payload = {"query": query, "session_id": session_id}
        return self._request("/api/v1/cognitive/intake", payload)

    def solve_logistics_selection(
        self,
        routes_or_warehouses: List[Dict[str, Any]],
        max_capacity: float,
        capacity_attribute: str = "weight",
        objective_attribute: str = "throughput",
        incompatible_pairs: Optional[List[List[str]]] = None,
        solver: str = "auto",
    ) -> Dict[str, Any]:
        """
        Optymalizacja logistyczna: wybór tras, hubów lub zleceń transportowych.
        """
        constraints = [
            {
                "name": "Maksymalna ładowność / przepustowość",
                "type": "budget",
                "attribute": capacity_attribute,
                "limit": max_capacity,
            }
        ]
        if incompatible_pairs:
            for pair in incompatible_pairs:
                if len(pair) == 2:
                    constraints.append({
                        "name": f"Wykluczenie wzajemne {pair[0]} vs {pair[1]}",
                        "type": "incompatible",
                        "var_ids": pair,
                    })

        return self.solve(
            title="Optymalizacja Logistyczna",
            domain="logistics",
            variables=routes_or_warehouses,
            constraints=constraints,
            objective_direction="maximize",
            objective_attribute=objective_attribute,
            solver=solver,
        )

    def solve_staff_allocation(
        self,
        candidates: List[Dict[str, Any]],
        team_size: int,
        max_budget: Optional[float] = None,
        cost_attribute: str = "cost",
        synergy_score_attribute: str = "score",
        mandatory_ids: Optional[List[str]] = None,
        solver: str = "auto",
    ) -> Dict[str, Any]:
        """
        Optymalny dobór personelu / zespołu projektowego.
        """
        constraints: List[Dict[str, Any]] = [
            {
                "name": f"Dokładny rozmiar zespołu: {team_size}",
                "type": "cardinality_exact",
                "count": team_size,
            }
        ]
        if max_budget is not None:
            constraints.append({
                "name": "Limit budżetu wynagrodzeń",
                "type": "budget",
                "attribute": cost_attribute,
                "limit": max_budget,
            })
        if mandatory_ids:
            for mid in mandatory_ids:
                constraints.append({
                    "name": f"Wymagana obecność {mid}",
                    "type": "linear",
                    "linear_lhs": {mid: 1.0},
                    "linear_op": "==",
                    "linear_rhs": 1.0,
                })

        return self.solve(
            title="Optymalny Dobór Zespołu",
            domain="hr",
            variables=candidates,
            constraints=constraints,
            objective_direction="maximize",
            objective_attribute=synergy_score_attribute,
            solver=solver,
        )
