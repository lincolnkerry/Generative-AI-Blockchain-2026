"""Scenario: Web chat frontend testing.

Tests the chat UI served at GET /.
Environment: Docker Compose up (db + api on localhost:8787).

Run:
    docker compose up -d && sleep 8
    pytest tests/scenarios/test_web_chat.py -v
"""

from __future__ import annotations

import httpx

BASE = "http://localhost:8787"

# Create a test API key
from server.api.auth import create_api_key
from db.session import get_session, init_db
from db.models import ApiKey, Provider
import db.models  # noqa: F401

init_db()

def _get_auth_headers() -> dict:
    raw, hashed = create_api_key()
    session = get_session()
    try:
        provider = session.get(Provider, "test-provider")
        if not provider:
            provider = Provider(id="test-provider", name="test", provider_type="openrouter", is_active=True)
            session.add(provider)
            session.commit()
        key = ApiKey(provider_id="test-provider", name="test-key", key_hash=hashed, prefix=raw[:8], is_active=True)
        session.add(key)
        session.commit()
    finally:
        session.close()
    return {"Authorization": f"Bearer {raw}"}

AUTH_HEADERS = _get_auth_headers()


class TestChatUI:
    """Web chat UI served at GET /."""

    def test_serves_html(self):
        resp = httpx.get(f"{BASE}/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")

    def test_contains_privacy_router_title(self):
        resp = httpx.get(f"{BASE}/")
        assert "Privacy Router" in resp.text

    def test_contains_chat_elements(self):
        resp = httpx.get(f"{BASE}/")
        html = resp.text.lower()
        # Should have input area and send mechanism
        assert "textarea" in html or "input" in html

    def test_contains_api_reference(self):
        resp = httpx.get(f"{BASE}/")
        html = resp.text
        # Should reference the API endpoint
        assert "/v1/chat/completions" in html or "chat/completions" in html


class TestChatAPIIntegration:
    """Chat UI → API integration (what the UI calls)."""

    def test_chat_completions_non_sensitive(self):
        resp = httpx.post(
            f"{BASE}/v1/chat/completions",
            json={
                "model": "privacy-router/openrouter/mistralai/ministral-3b-2512",
                "messages": [{"role": "user", "content": "안녕하세요"}],
                "max_tokens": 32,
            },
            headers=AUTH_HEADERS,
        )
        assert resp.status_code in (200, 502)
    def test_chat_completions_sensitive_returns_response(self):
        resp = httpx.post(
            f"{BASE}/v1/chat/completions",
            json={
                "model": "privacy-router/openrouter/mistralai/ministral-3b-2512",
                "messages": [{"role": "user", "content": "주민등록번호 901212-1234567을 확인해주세요"}],
                "max_tokens": 32,
            },
            headers=AUTH_HEADERS,
        )
        # Pipeline handles sensitive input — returns 200 (masked), 409 (prompt_user), or 502 (LLM error)
        assert resp.status_code in (200, 409, 502)
        if resp.status_code == 200:
            data = resp.json()
            assert "choices" in data or "privacy_router" in data
