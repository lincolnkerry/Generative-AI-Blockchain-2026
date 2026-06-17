"""Scenario: OpenAPI endpoint testing.

Tests all REST API endpoints against a running Privacy Router server.
Environment: Docker Compose up (db + api on localhost:8787).

Run:
    docker compose up -d && sleep 8
    pytest tests/scenarios/test_openapi.py -v
"""

from __future__ import annotations

import httpx

BASE = "http://localhost:8787"

# Create a test API key via the auth module
from server.api.auth import create_api_key
from db.session import get_session, init_db
from db.models import ApiKey, Provider
import db.models  # noqa: F401

init_db()

def _get_auth_headers() -> dict:
    """Create a test API key and return auth headers."""
    raw, hashed = create_api_key()
    session = get_session()
    try:
        # Ensure test provider exists
        provider = session.get(Provider, "test-provider")
        if not provider:
            provider = Provider(id="test-provider", name="test", provider_type="openrouter", is_active=True)
            session.add(provider)
            session.commit()
        # Create key
        key = ApiKey(provider_id="test-provider", name="test-key", key_hash=hashed, prefix=raw[:8], is_active=True)
        session.add(key)
        session.commit()
    finally:
        session.close()
    return {"Authorization": f"Bearer {raw}"}

AUTH_HEADERS = _get_auth_headers()


# ── Public endpoints (no auth) ───────────────────────────────────────────────


class TestPublic:
    """Endpoints accessible without authentication."""

    def test_swagger_ui(self):
        resp = httpx.get(f"{BASE}/docs")
        assert resp.status_code == 200
        assert "swagger-ui" in resp.text.lower()

    def test_openapi_schema(self):
        resp = httpx.get(f"{BASE}/openapi.json")
        assert resp.status_code == 200
        paths = resp.json()["paths"]
        assert "/v1/chat/completions" in paths
        assert "/api/v1/classify" in paths
        assert "/api/v1/masking/{session_id}" in paths

    def test_v1_models(self):
        resp = httpx.get(f"{BASE}/v1/models")
        assert resp.status_code == 200
        assert resp.json()["object"] == "list"

    def test_settings(self):
        resp = httpx.get(f"{BASE}/api/settings")
        assert resp.status_code == 200


# ── API Key management ───────────────────────────────────────────────────────


class TestAPIKeys:
    """API key CRUD."""

    def test_create_key(self):
        resp = httpx.post(
            f"{BASE}/api/v1/keys",
            json={"name": "scenario-test-key", "provider_id": "test-provider"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["api_key"].startswith("pr-")

    def test_list_keys(self):
        resp = httpx.get(
            f"{BASE}/api/v1/keys",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# ── Model registry ───────────────────────────────────────────────────────────


class TestModelRegistry:
    """Model CRUD."""

    def test_list_models(self):
        resp = httpx.get(
            f"{BASE}/api/v1/models",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200

    def test_create_model(self):
        resp = httpx.post(
            f"{BASE}/api/v1/models",
            json={"model_id": "test/scenario-model", "provider_id": "test-provider", "tier": "edge"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 201


# ── Provider management ──────────────────────────────────────────────────────


class TestProviders:
    """Provider CRUD."""

    def test_list_providers(self):
        resp = httpx.get(
            f"{BASE}/api/v1/providers",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200


# ── Classify endpoint ────────────────────────────────────────────────────────


class TestClassify:
    """POST /api/v1/classify — extract + judge."""

    def test_sensitive_input(self):
        resp = httpx.post(
            f"{BASE}/api/v1/classify",
            json={"text": "주민등록번호 901212-1234567을 확인해주세요"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_sensitive"] is True
        assert len(data["extraction_records"]) > 0

    def test_non_sensitive_input(self):
        resp = httpx.post(
            f"{BASE}/api/v1/classify",
            json={"text": "오늘 서울 날씨는 맑습니다"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["is_sensitive"] is False


# ── Masking endpoints ────────────────────────────────────────────────────────


class TestMasking:
    """GET /api/v1/masking/{id} and POST /api/v1/masking/{id}/hydrate."""

    def test_get_nonexistent(self):
        resp = httpx.get(
            f"{BASE}/api/v1/masking/nonexistent",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 404

    def test_hydrate_nonexistent(self):
        resp = httpx.post(
            f"{BASE}/api/v1/masking/nonexistent/hydrate",
            json={"content": "test"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 404

    def test_hydrate_missing_content(self):
        resp = httpx.post(
            f"{BASE}/api/v1/masking/nonexistent/hydrate",
            json={},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 400
