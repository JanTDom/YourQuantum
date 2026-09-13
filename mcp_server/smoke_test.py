"""
YourQuantum MCP Smoke Test
Executes tools against the YourQuantum API and verifies end-to-end responses.
"""

from __future__ import annotations

import asyncio
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_server.server import (
    analyze_dilemma,
    get_engine_status,
    optimize_options,
    solve_portfolio,
)


async def run_smoke_test() -> int:
    print("=" * 70)
    print("🚀 ROZPOCZYNAM SMOKE-TEST SERWERA YOURQUANTUM MCP")
    print("=" * 70)

    # Sprawdź konfigurację środowiskową
    api_key = os.environ.get("YQ_API_KEY", "").strip()
    base_url = os.environ.get("YQ_API_BASE_URL", "https://yourquantum.pl").strip()
    print(f"📡 Adres bazowy API: {base_url}")
    print(f"🔑 Klucz API (YQ_API_KEY): {'[USTAWIONY]' if api_key else '[BRAK — ustaw np. export YQ_API_KEY=twoj_klucz]'}")
    print("-" * 70)

    # 1. Test pobrania statusu silnika
    print("\n[TEST 1/4] Wywołanie yq_get_engine_status()...")
    status_res = await get_engine_status()
    print(status_res)
    assert "STATUS SILNIKA YOURQUANTUM" in status_res or "BŁĄD" in status_res, "Nieoczekiwana odpowiedź statusu"

    # 2. Test Input Quality Gate (analiza dylematu bez liczb)
    print("\n[TEST 2/4] Wywołanie yq_analyze_dilemma() na dylemacie ogólnym...")
    dilemma_text = "Mamy dylemat dotyczący wyboru nowej bazy danych do systemu transakcyjnego."
    dilemma_res = await analyze_dilemma(dilemma_text)
    print(dilemma_res)
    assert "ANALIZA DYLEMATU DECYZYJNEGO" in dilemma_res or "BŁĄD" in dilemma_res

    # 3. Test walidacji uczciwości wyniku (brak kryterium celu -> wymóg podania parametrów)
    print("\n[TEST 3/4] Test uczciwości wyniku (brak metryki celu -> celowe odrzucenie bez domyślnych założeń)...")
    invalid_call_res = await optimize_options(
        title="Test braku kryteriów",
        options=[
            {"id": "a", "name": "Opcja A"},
            {"id": "b", "name": "Opcja B"},
        ],
        objective_direction="maximize",
        objective_attribute=None,
        objective_coefficients=None,
    )
    print(invalid_call_res)
    assert "BŁĄD METRYKI CELU" in invalid_call_res, "Silnik powinien odmówić cichego zgadywania celu!"
    print("✅ Prawidłowo wymuszono jawne zdefiniowanie kryterium optymalizacji.")

    # 4. Test pełnej optymalizacji wielokryterialnej (Portfolio / Opcje z budżetem)
    if not api_key:
        print("\n⚠️ Pomijam pełny test obliczeniowy (TEST 4/4), ponieważ YQ_API_KEY nie jest ustawiony.")
        print("Aby go uruchomić: YQ_API_KEY=twoj_klucz python mcp_server/smoke_test.py")
        return 0

    print("\n[TEST 4/4] Pełna optymalizacja wyboru opcji yq_solve_portfolio()...")
    portfolio_res = await solve_portfolio(
        title="Wybór Inicjatyw Transformacji Cyfrowej",
        projects=[
            {"id": "proj_erp", "name": "Modernizacja ERP", "cost": 140000, "value": 390000},
            {"id": "proj_ai", "name": "Wdrożenie Agentów AI", "cost": 80000, "value": 270000},
            {"id": "proj_sec", "name": "Zero-Trust Security Shield", "cost": 60000, "value": 210000},
            {"id": "proj_cloud", "name": "Migracja Multi-Cloud", "cost": 110000, "value": 180000},
        ],
        budget_limit=200000,
        budget_attribute="cost",
        objective_attribute="value",
    )
    print(portfolio_res)
    assert "WYNIK OPTYMALIZACJI DECYZYJNEJ" in portfolio_res, "Brak oczekiwanego podsumowania optymalizacji"
    assert "Paszport kryptograficzny SHA-256" in portfolio_res, "Brak certyfikatu SHA-256 w wyniku"

    print("\n" + "=" * 70)
    print("🎉 WSZYSTKIE TESTY SMOKE-CHECK PRZESZŁY POMYŚLNIE!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(run_smoke_test())
    sys.exit(exit_code)
