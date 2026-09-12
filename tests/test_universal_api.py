"""
tests/test_universal_api.py

Kompleksowe testy dla zabezpieczonego Uniwersalnego API i SDK:
1. Weryfikacja hasła dostępu: poprawne hasło 'A132a132!' zwraca token, błędne hasło daje 401.
2. Pobieranie SDK: endpoint /api/v1/sdk/download zwraca kompletny kod Python i TypeScript.
3. Wielozadaniowe obliczenia w różnych dziedzinach:
   - Finanse: Optymalizacja portfela inwestycyjnego z limitem budżetowym
   - Logistyka: Wybór tras transportowych z wykluczeniami wzajemnymi
   - HR / Zespoły: Dobór składu osobowego z ograniczeniami liczebności
4. Niezależny certyfikat SHA-256 i raport wrażliwości na szok w odpowiedzi uniwersalnej.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app
from backend.db.database import init_db
from backend.api.universal_engine import verify_master_secret, MASTER_API_SECRET


def test_master_secret_verification():
    """Testuje stałoczasową weryfikację hasła."""
    assert verify_master_secret("A132a132!") is True
    assert verify_master_secret("Bearer A132a132!") is True
    assert verify_master_secret("zle_haslo") is False
    assert verify_master_secret("") is False


@pytest.mark.asyncio
async def test_auth_verify_api_access_endpoint():
    """Weryfikuje endpoint /api/v1/auth/verify-api-access."""
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Błędne hasło -> 401
        res_bad = await client.post(
            "/api/v1/auth/verify-api-access",
            json={"password": "niepoprawne_haslo_123"},
        )
        assert res_bad.status_code == 401
        assert "Nieprawidłowe hasło" in res_bad.json()["detail"]

        # Prawidłowe hasło A132a132! -> 200 + token
        res_ok = await client.post(
            "/api/v1/auth/verify-api-access",
            json={"password": "A132a132!"},
        )
        assert res_ok.status_code == 200
        data = res_ok.json()
        assert data["valid"] is True
        assert data["token"].startswith("yq_live_master_")


@pytest.mark.asyncio
async def test_sdk_download_endpoint_protection():
    """Sprawdza ochronę i pobieranie SDK Pythona i TypeScript."""
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Próba pobrania bez autoryzacji -> 401
        res_noauth = await client.get("/api/v1/sdk/download?sdk_type=python")
        assert res_noauth.status_code == 401

        # Pobranie SDK Python z hasłem -> 200 + zawartość pliku
        res_py = await client.get("/api/v1/sdk/download?sdk_type=python&key=A132a132!")
        assert res_py.status_code == 200
        assert "YourQuantumClient" in res_py.text
        assert "solve_portfolio" in res_py.text

        # Pobranie SDK TypeScript z hasłem -> 200 + zawartość pliku
        res_ts = await client.get("/api/v1/sdk/download?sdk_type=typescript&key=A132a132!")
        assert res_ts.status_code == 200
        assert "export class YourQuantumClient" in res_ts.text
        assert "UniversalComputeResponse" in res_ts.text


@pytest.mark.asyncio
async def test_universal_compute_finance_portfolio():
    """
    Wielozadaniowe API: Optymalizacja portfela inwestycji.
    Budżet 220 000 zł.
    Projekty:
    - P1: koszt 150k, zysk 420k
    - P2: koszt 90k, zysk 230k
    - P3: koszt 60k, zysk 195k
    - P4: koszt 120k, zysk 180k
    
    Kombinacje:
    P1 + P3 = 210k <= 220k, zysk = 615k (OPTYMUM)
    P2 + P3 = 150k <= 220k, zysk = 425k
    P1 + P2 = 240k > 220k (niedopuszczalne)
    """
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "domain": "finance",
            "title": "Alokacja Kapitału w Projekty B+R",
            "variables": [
                {"id": "p1", "name": "Nowa linia produkcyjna", "cost": 150000.0, "value": 420000.0},
                {"id": "p2", "name": "Ekspansja magazynowa", "cost": 90000.0, "value": 230000.0},
                {"id": "p3", "name": "Automatyzacja AI", "cost": 60000.0, "value": 195000.0},
                {"id": "p4", "name": "Flota elektryczna", "cost": 120000.0, "value": 180000.0},
            ],
            "objective_direction": "maximize",
            "objective_attribute": "value",
            "constraints": [
                {
                    "name": "Limit budżetowy",
                    "type": "budget",
                    "attribute": "cost",
                    "limit": 220000.0,
                }
            ],
            "solver": "auto",
            "include_stress_test": True,
        }

        # Wywołanie z nagłówkiem autoryzacyjnym
        res = await client.post(
            "/api/v1/universal/compute",
            headers={"Authorization": "Bearer A132a132!"},
            json=payload,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "SUCCESS"
        assert data["optimal_assignment"]["p1"] == 1
        assert data["optimal_assignment"]["p3"] == 1
        assert data["optimal_assignment"]["p2"] == 0
        assert data["optimal_assignment"]["p4"] == 0
        assert data["total_objective_value"] == 615000.0
        assert data["verification"]["feasible"] is True
        assert len(data["sha256_passport"]) == 64
        assert data["sensitivity_report"] is not None


@pytest.mark.asyncio
async def test_universal_compute_logistics_with_conflicts():
    """
    Wielozadaniowe API: Wybór tras logistycznych z wykluczeniem wzajemnym.
    Trasy T1 i T2 wykluczają się (wspólny korytarz).
    Wybieramy dokładnie 2 trasy o największej przepustowości.
    T1: 100, T2: 90, T3: 80, T4: 70.
    T1 i T2 nie mogą być wybrane razem, więc optimum to T1 (100) + T3 (80) = 180.
    """
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "domain": "logistics",
            "title": "Optymalizacja Przydziału Tras",
            "variables": [
                {"id": "t1", "name": "Trasa Północ A", "value": 100.0},
                {"id": "t2", "name": "Trasa Północ B", "value": 90.0},
                {"id": "t3", "name": "Trasa Południe", "value": 80.0},
                {"id": "t4", "name": "Trasa Wschód", "value": 70.0},
            ],
            "objective_direction": "maximize",
            "objective_attribute": "value",
            "constraints": [
                {
                    "name": "Dokładnie 2 trasy",
                    "type": "cardinality_exact",
                    "count": 2,
                },
                {
                    "name": "Wykluczenie wzajemne T1 i T2",
                    "type": "incompatible",
                    "var_ids": ["t1", "t2"],
                },
            ],
            "solver": "auto",
        }

        res = await client.post(
            "/api/v1/universal/compute",
            headers={"X-API-Key": "A132a132!"},
            json=payload,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "SUCCESS"
        assert data["optimal_assignment"]["t1"] == 1
        assert data["optimal_assignment"]["t3"] == 1
        assert data["optimal_assignment"]["t2"] == 0
        assert data["total_objective_value"] == 180.0
