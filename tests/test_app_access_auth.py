"""
Tests for server-side app access gate (V9-B).
"""

import os
import secrets
import time
from pathlib import Path
import pytest
from starlette.testclient import TestClient

from backend.main import app
from backend.api.routes import _FAILED_APP_AUTH_ATTEMPTS
from backend.api.universal_engine import create_app_expiring_token


@pytest.fixture(autouse=True)
def clean_failed_attempts():
    """Wyczyść licznik nieudanych prób logowania przed każdym testem."""
    _FAILED_APP_AUTH_ATTEMPTS.clear()
    yield
    _FAILED_APP_AUTH_ATTEMPTS.clear()


def test_app_auth_success_with_random_secret(monkeypatch):
    """Poprawne hasło z losowej zmiennej środowiskowej (brak literału) -> 200 i wydanie tokenu."""
    random_secret = secrets.token_hex(16)
    monkeypatch.setenv("YQ_APP_ACCESS_SECRET", random_secret)

    client = TestClient(app)
    resp = client.post("/api/v1/auth/verify-app-access", json={"password": random_secret})

    assert resp.status_code == 200
    data = resp.json()
    assert data.get("valid") is True
    assert "token" in data
    assert data["token"].startswith("yq_app_exp_")


def test_app_auth_bad_password_returns_401(monkeypatch):
    """Niepoprawne hasło -> 401."""
    random_secret = secrets.token_hex(16)
    monkeypatch.setenv("YQ_APP_ACCESS_SECRET", random_secret)

    client = TestClient(app)
    resp = client.post("/api/v1/auth/verify-app-access", json={"password": "wrong_password"})

    assert resp.status_code == 401
    assert "Nieprawidłowe hasło" in resp.json().get("detail", "")


def test_app_auth_missing_env_returns_503(monkeypatch):
    """Brak zmiennej środowiskowej YQ_APP_ACCESS_SECRET -> 503."""
    monkeypatch.delenv("YQ_APP_ACCESS_SECRET", raising=False)

    client = TestClient(app)
    resp = client.post("/api/v1/auth/verify-app-access", json={"password": "any_password"})

    assert resp.status_code == 503
    assert "Brama aplikacji nie jest skonfigurowana" in resp.json().get("detail", "")


def test_app_auth_rate_limiting_lockout_on_sixth_attempt(monkeypatch):
    """5 nieudanych prób z rzędu z tego samego IP, 6. próba zwraca 429 przez 15 minut."""
    random_secret = secrets.token_hex(16)
    monkeypatch.setenv("YQ_APP_ACCESS_SECRET", random_secret)

    client = TestClient(app)
    # Próby 1 do 5 kończą się 401
    for i in range(5):
        resp = client.post("/api/v1/auth/verify-app-access", json={"password": f"bad_pwd_{i}"})
        assert resp.status_code == 401

    # Szósta próba (nawet z poprawnym hasłem!) powinna zostać zablokowana kodem 429
    resp_sixth = client.post("/api/v1/auth/verify-app-access", json={"password": random_secret})
    assert resp_sixth.status_code == 429
    assert "Zbyt wiele nieudanych prób logowania" in resp_sixth.json().get("detail", "")


def test_app_auth_validate_valid_token(monkeypatch):
    """Ważny token wydany wcześniej -> 200."""
    random_secret = secrets.token_hex(16)
    monkeypatch.setenv("YQ_APP_ACCESS_SECRET", random_secret)

    token = create_app_expiring_token(random_secret, ttl_hours=24)

    client = TestClient(app)
    resp = client.post("/api/v1/auth/verify-app-access", json={"token": token})
    assert resp.status_code == 200
    assert resp.json().get("valid") is True


def test_app_auth_expired_token_rejected(monkeypatch):
    """Wygasły token (ttl ujemny) -> 401."""
    random_secret = secrets.token_hex(16)
    monkeypatch.setenv("YQ_APP_ACCESS_SECRET", random_secret)

    # Token wygasły godzinę temu
    expired_token = create_app_expiring_token(random_secret, ttl_hours=-1)

    client = TestClient(app)
    resp = client.post("/api/v1/auth/verify-app-access", json={"token": expired_token})
    assert resp.status_code == 401
    assert "wygasł" in resp.json().get("detail", "").lower()


def test_no_authorized_hashes_in_frontend():
    """Wymóg V9-B: stała AUTHORIZED_HASHES nie występuje w żadnym pliku w frontend/src."""
    frontend_src = Path(__file__).resolve().parent.parent / "frontend" / "src"
    assert frontend_src.is_dir()

    hits = []
    for file_path in frontend_src.rglob("*"):
        if file_path.is_file() and file_path.suffix in (".ts", ".tsx", ".js", ".jsx"):
            content = file_path.read_text(encoding="utf-8")
            if "AUTHORIZED_HASHES" in content:
                hits.append(str(file_path.relative_to(frontend_src)))

    assert hits == [], f"Znaleziono AUTHORIZED_HASHES w plikach frontendu: {hits}"
