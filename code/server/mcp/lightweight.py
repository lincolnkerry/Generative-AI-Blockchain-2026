"""Privacy Router MCP Server — lightweight HTTP client.

This is a thin MCP server that calls the Privacy Router HTTP API
instead of importing the full server stack. This avoids dependency
issues in agent containers (Hermes, OpenClaw).
"""

from __future__ import annotations

import os

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("privacy-router")

API_BASE = os.environ.get("PRIVACY_ROUTER_URL", "http://api:8787")
API_KEY = os.environ.get("PRIVACY_ROUTER_API_KEY", "pr-demo-key")


@mcp.tool()
def process(
    text: str,
    action: str = "auto",
    model: str | None = None,
    chat_id: str | None = None,
) -> dict:
    """Process a prompt through the Privacy Router pipeline.

    Args:
        text: The raw prompt to process.
        action: "auto" | "classify" | "generate" | "allow" | "hydrate"
        model: Override the generator model.
        chat_id: Optional chat ID for masking session tracking.

    Returns:
        dict with action_taken, content, records, policy_action, etc.
    """
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

    if action == "classify":
        resp = httpx.post(
            f"{API_BASE}/api/v1/classify",
            json={"text": text},
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    if action == "generate":
        resp = httpx.post(
            f"{API_BASE}/api/v1/generate",
            json={"text": text, "model": model},
            headers=headers,
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()

    # Default: auto — use classify + generate
    classify_resp = httpx.post(
        f"{API_BASE}/api/v1/classify",
        json={"text": text},
        headers=headers,
        timeout=30,
    )
    classify_resp.raise_for_status()
    classify_data = classify_resp.json()

    if not classify_data.get("is_sensitive", False):
        # No sensitive info — pass through directly
        return {
            "action_taken": "allow",
            "content": None,
            "extraction_records": [],
            "policy_action": "route_to_external",
            "is_sensitive": False,
            "requires_masking": False,
            "model_used": None,
            "latency_ms": 0.0,
        }

    # Sensitive — run generate (which masks + forwards)
    gen_resp = httpx.post(
        f"{API_BASE}/api/v1/generate",
        json={"text": text, "model": model},
        headers=headers,
        timeout=60,
    )
    gen_resp.raise_for_status()
    return gen_resp.json()


if __name__ == "__main__":
    mcp.run(transport="stdio")
