from __future__ import annotations

import importlib
import sys

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage


def test_health_imports_without_api_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_URL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY_DEFAULT", raising=False)

    sys.modules.pop("agent", None)

    try:
        agent_module = importlib.import_module("agent")
        result = agent_module.health()
    finally:
        sys.modules.pop("agent", None)

    assert result["ok"] is True
    assert result["name"] == "sdlc-copilot-agent"
    assert result["governed"] is False
    assert result["endpoints"]["chat"] == "POST /chat"
    assert result["endpoints"]["trigger"] == "POST /trigger"


def test_resolve_llm_config_byo(monkeypatch) -> None:
    from agent import _resolve_llm_config

    monkeypatch.delenv("OPENAI_URL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY_DEFAULT", "byo-key")

    cfg = _resolve_llm_config()

    assert cfg == {"api_key": "byo-key"}


def test_resolve_llm_config_governed(monkeypatch) -> None:
    from agent import _resolve_llm_config

    monkeypatch.setenv("OPENAI_URL", "https://gateway.example/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "am-key")
    monkeypatch.setenv("OPENAI_API_KEY_DEFAULT", "byo-key")

    cfg = _resolve_llm_config()

    assert cfg["base_url"] == "https://gateway.example/v1"
    assert cfg["api_key"] == "unused"
    assert cfg["default_headers"] == {"API-Key": "am-key", "Authorization": ""}


def test_truncate_preserves_non_tool_start() -> None:
    from agent import MAX_SESSION_MESSAGES, _truncate

    ai_tool_block = [
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "run_static_quality_scan",
                    "args": {"repository_url": "checkout-service"},
                    "id": "call-1",
                }
            ],
        ),
        ToolMessage(content='{"ok": true}', tool_call_id="call-1"),
        ToolMessage(content='{"ok": true}', tool_call_id="call-1"),
    ]
    rest = [HumanMessage(content=f"message {i}") for i in range(MAX_SESSION_MESSAGES)]

    result = _truncate(ai_tool_block + rest)

    assert len(result) <= MAX_SESSION_MESSAGES
    assert not isinstance(result[0], ToolMessage)


def test_trigger_deterministic_endpoint_without_llm() -> None:
    from agent import app

    client = TestClient(app)
    response = client.post(
        "/trigger",
        json={
            "repository_url": "checkout-service",
            "branch": "main",
            "analysis_type": "release_readiness",
            "change_summary": "Testing deterministic trigger path.",
            "use_llm": False,
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["analysis_id"].startswith("mock-")
    assert body["analysis_type"] == "release_readiness"
    assert "Decision:" in body["response"]
    assert "Mocked SDLC analysis" in body["response"]