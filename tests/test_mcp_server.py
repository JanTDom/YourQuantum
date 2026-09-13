"""
Tests for YourQuantum MCP Server and Tools.
Validates input sanitization, error messages, honesty enforcement, and tool executions.
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from mcp_server.client import YourQuantumApiClient, YourQuantumApiError
from mcp_server.server import (
    analyze_dilemma,
    get_engine_status,
    optimize_options,
    solve_portfolio,
)


@pytest.mark.asyncio
async def test_optimize_options_missing_title():
    res = await optimize_options(
        title="",
        options=[{"id": "1", "name": "A", "val": 10}, {"id": "2", "name": "B", "val": 20}],
        objective_direction="maximize",
        objective_attribute="val",
    )
    assert "BŁĄD WALIDACJI: Brak tytułu dylematu" in res


@pytest.mark.asyncio
async def test_optimize_options_less_than_two_options():
    res = await optimize_options(
        title="Dylemat",
        options=[{"id": "1", "name": "Tylko jedna"}],
        objective_direction="maximize",
        objective_attribute="cost",
    )
    assert "BŁĄD WALIDACJI: Do porównania i optymalizacji wymagane są co najmniej 2 warianty" in res


@pytest.mark.asyncio
async def test_optimize_options_rejects_silent_defaults_when_objective_missing():
    """Verify honesty rule: reject if neither objective_attribute nor objective_coefficients are given."""
    res = await optimize_options(
        title="Dylemat bez celu",
        options=[{"id": "1", "name": "A"}, {"id": "2", "name": "B"}],
        objective_direction="maximize",
        objective_attribute=None,
        objective_coefficients=None,
    )
    assert "BŁĄD METRYKI CELU: Nie określono kryterium optymalizacji" in res


@pytest.mark.asyncio
async def test_optimize_options_missing_attribute_in_option():
    res = await optimize_options(
        title="Dylemat",
        options=[
            {"id": "1", "name": "A", "roi": 100},
            {"id": "2", "name": "B"},  # missing roi
        ],
        objective_direction="maximize",
        objective_attribute="roi",
    )
    assert "BŁĄD BRAKUJĄCEJ WARTOŚCI: Opcja 'B'" in res


@pytest.mark.asyncio
async def test_optimize_options_budget_missing_attribute():
    res = await optimize_options(
        title="Dylemat",
        options=[{"id": "1", "name": "A", "val": 10}, {"id": "2", "name": "B", "val": 20}],
        objective_direction="maximize",
        objective_attribute="val",
        budget_limit=100.0,
        budget_attribute=None,
    )
    assert "BŁĄD OGRANICZENIA: Podano limit zasobu" in res


@pytest.mark.asyncio
async def test_solve_portfolio_missing_numbers():
    res = await solve_portfolio(
        title="Portfel",
        projects=[
            {"id": "1", "name": "Projekt A", "cost": 1000, "value": 2000},
            {"id": "2", "name": "Projekt B"},  # missing value and cost
        ],
        budget_limit=5000,
    )
    assert "BŁĄD DANYCH: Projekt 'Projekt B' nie posiada określonego kosztu" in res


@pytest.mark.asyncio
async def test_analyze_dilemma_short_text():
    res = await analyze_dilemma("ab")
    assert "BŁĄD WALIDACJI: Treść dylematu (`description`) musi mieć co najmniej 5 znaków." in res


@pytest.mark.asyncio
async def test_client_missing_api_key_raises_error():
    client = YourQuantumApiClient(api_key="")
    with pytest.raises(YourQuantumApiError) as exc:
        await client.universal_compute({"title": "Test", "variables": []})
    assert "BŁĄD AUTORYZACJI: Brak zmiennej środowiskowej YQ_API_KEY" in str(exc.value)


@pytest.mark.asyncio
async def test_optimize_options_mocked_success():
    mock_response = {
        "status": "SUCCESS",
        "optimal_selection": [{"id": "opt_1", "name": "Opcja 1", "value": 50.0, "attributes": {}}],
        "total_objective_value": 50.0,
        "solver_used": "cpsat",
        "optimality_proven": True,
        "sha256_passport": "mock_sha_123456",
        "sensitivity_report": {"robustness_score": 92.0, "verdict": "RESILIENT", "summary_pl": "Odporne na wstrząsy."},
    }
    with patch.object(YourQuantumApiClient, "universal_compute", new_callable=AsyncMock) as mock_comp:
        mock_comp.return_value = mock_response
        res = await optimize_options(
            title="Wybór architektury",
            options=[
                {"id": "opt_1", "name": "Opcja 1", "value": 50.0},
                {"id": "opt_2", "name": "Opcja 2", "value": 30.0},
            ],
            objective_direction="maximize",
            objective_attribute="value",
        )
        assert "WYNIK OPTYMALIZACJI DECYZYJNEJ YOURQUANTUM" in res
        assert "Opcja 1" in res
        assert "Odrzucone warianty alternatywne" in res
        assert "Opcja 2" in res
        assert "mock_sha_123456" in res
        assert "RESILIENT" in res


@pytest.mark.asyncio
async def test_cognitive_intake_tool_mocked():
    from mcp_server.server import cognitive_intake
    mock_response = {
        "status": "ready_for_review",
        "explanation": "Kognitywna formalizacja dylematu R&D",
        "questions": [],
        "confidence": 0.95,
        "problem_ir": {
            "variables": [{"id": "v1"}, {"id": "v2"}],
            "constraints": [{"id": "c1"}],
            "objectives": [{"direction": "maximize"}],
        },
    }
    with patch.object(YourQuantumApiClient, "cognitive_intake", new_callable=AsyncMock) as mock_intake:
        mock_intake.return_value = mock_response
        res = await cognitive_intake("Wybór projektów R&D przy budżecie 100k")
        assert "KOGNITYWNY MÓZG DECYZYJNY YOURQUANTUM" in res
        assert "READY_FOR_REVIEW" in res
        assert "95%" in res
        assert "**Liczba zmiennych decyzyjnych**: 2" in res
