"""
YourQuantum API Client for MCP Server
Provides robust, typed, and error-resilient HTTP communications with YourQuantum API.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger("yourquantum-mcp")


class YourQuantumApiError(Exception):
    """Custom exception raised when an API call fails with actionable explanation."""
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


class YourQuantumApiClient:
    """HTTP client communicating with YourQuantum REST API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 45.0,
    ):
        self.base_url = (base_url or os.environ.get("YQ_API_BASE_URL", "https://yourquantum.pl")).rstrip("/")
        self.api_key = (api_key or os.environ.get("YQ_API_KEY", "")).strip()
        self.timeout = timeout

    def _get_headers(self, require_auth: bool = True) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "YourQuantum-MCP-Server/1.0.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            headers["X-API-Key"] = self.api_key
        elif require_auth:
            raise YourQuantumApiError(
                "BŁĄD AUTORYZACJI: Brak zmiennej środowiskowej YQ_API_KEY. "
                "Ustaw poprawny klucz dostępu w zmiennych środowiskowych serwera MCP (np. w konfiguracji Claude w sekcji 'env')."
            )
        return headers

    async def get_solvers_health(self) -> Dict[str, Any]:
        """Fetch available solvers and health status (public endpoint)."""
        url = f"{self.base_url}/api/v1/health/solvers"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.get(url, headers=self._get_headers(require_auth=False))
                resp.raise_for_status()
                return resp.json()
            except httpx.TimeoutException:
                raise YourQuantumApiError("BŁĄD TIMEOUTU: Serwer YourQuantum nie odpowiedział w zadanym czasie na sprawdzenie stanu solverów.")
            except httpx.ConnectError:
                raise YourQuantumApiError(f"BŁĄD POŁĄCZENIA: Nie można połączyć się z serwerem pod adresem {self.base_url}.")
            except httpx.HTTPStatusError as e:
                raise YourQuantumApiError(f"BŁĄD HTTP {e.response.status_code}: {e.response.text}", status_code=e.response.status_code)
            except Exception as e:
                raise YourQuantumApiError(f"BŁĄD SIECIOWY: {str(e)}")

    async def analyze_dilemma(self, text: str) -> Dict[str, Any]:
        """Analyze a decision problem using YourQuantum Input Quality Gate."""
        url = f"{self.base_url}/api/v1/cases/analyze"
        payload = {"text": text}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.post(url, json=payload, headers=self._get_headers(require_auth=False))
                resp.raise_for_status()
                return resp.json()
            except httpx.TimeoutException:
                raise YourQuantumApiError("BŁĄD TIMEOUTU: Przekroczono limit czasu analizy dylematu na serwerze.")
            except httpx.ConnectError:
                raise YourQuantumApiError(f"BŁĄD POŁĄCZENIA: Nie można połączyć się z adresem {self.base_url}.")
            except httpx.HTTPStatusError as e:
                raise YourQuantumApiError(f"BŁĄD HTTP {e.response.status_code}: {e.response.text}", status_code=e.response.status_code)
            except Exception as e:
                raise YourQuantumApiError(f"BŁĄD ZAPYTANIA: {str(e)}")

    async def cognitive_intake(self, query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Formalize a natural language dilemma through the Brain-Inspired Cognitive Architecture."""
        url = f"{self.base_url}/api/v1/cognitive/intake"
        payload = {"query": query, "session_id": session_id}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.post(url, json=payload, headers=self._get_headers(require_auth=False))
                resp.raise_for_status()
                return resp.json()
            except httpx.TimeoutException:
                raise YourQuantumApiError("BŁĄD TIMEOUTU: Przekroczono limit czasu orkiestracji kognitywnej na serwerze.")
            except httpx.ConnectError:
                raise YourQuantumApiError(f"BŁĄD POŁĄCZENIA: Nie można połączyć się z adresem {self.base_url}.")
            except httpx.HTTPStatusError as e:
                raise YourQuantumApiError(f"BŁĄD HTTP {e.response.status_code}: {e.response.text}", status_code=e.response.status_code)
            except Exception as e:
                raise YourQuantumApiError(f"BŁĄD ZAPYTANIA: {str(e)}")

    async def universal_compute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a multi-domain optimization request (requires YQ_API_KEY)."""
        url = f"{self.base_url}/api/v1/universal/compute"
        headers = self._get_headers(require_auth=True)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code == 401 or resp.status_code == 403:
                    raise YourQuantumApiError(
                        f"BŁĄD AUTORYZACJI (HTTP {resp.status_code}): Podany klucz YQ_API_KEY jest nieprawidłowy lub nie ma uprawnień do silnika obliczeniowego.",
                        status_code=resp.status_code,
                    )
                if resp.status_code == 422:
                    try:
                        err_json = resp.json()
                        detail = err_json.get("detail", resp.text)
                    except Exception:
                        detail = resp.text
                    raise YourQuantumApiError(
                        f"BŁĄD WALIDACJI MODELU (HTTP 422): Parametry wejściowe zostały odrzucone przez silnik matematyczny. Szczegóły: {detail}",
                        status_code=422,
                        details=detail,
                    )
                if resp.status_code >= 500:
                    raise YourQuantumApiError(
                        f"BŁĄD SERWERA YOURQUANTUM (HTTP {resp.status_code}): Wewnętrzny błąd silnika obliczeniowego. {resp.text}",
                        status_code=resp.status_code,
                    )
                resp.raise_for_status()
                return resp.json()
            except httpx.TimeoutException:
                raise YourQuantumApiError(
                    "BŁĄD TIMEOUTU: Obliczenia przekroczyły limit 45 sekund. "
                    "Zadanie kombinatoryczne może mieć zbyt dużą przestrzeń stanów lub nałożono zbyt gęste ograniczenia."
                )
            except httpx.ConnectError:
                raise YourQuantumApiError(
                    f"BŁĄD POŁĄCZENIA: Nie można nawiązać połączenia z serwerem YourQuantum pod adresem {self.base_url}."
                )
            except YourQuantumApiError:
                raise
            except Exception as e:
                raise YourQuantumApiError(f"NIEOCZEKIWANY BŁĄD PODCZAS OBLICZEŃ: {str(e)}")
