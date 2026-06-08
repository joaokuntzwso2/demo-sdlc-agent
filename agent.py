"""SDLC Copilot agent.

FastAPI service exposing:

1. POST /chat
   Interactive chat endpoint compatible with the WSO2 Agent Manager
   Platform-Hosted Agent chat contract.

   Request:
       {"message": "string", "session_id": "string", "context": {}}

   Response:
       {"response": "string"}

2. POST /trigger
   Non-interactive one-shot trigger endpoint. It creates a deterministic
   analysis request, invokes the same agent/tooling path, and returns the
   final answer without requiring a conversation.

3. GET /health
   Readiness and configuration signal.

Conversation state is kept server-side by session_id. This is intentionally
in-memory for demo simplicity. Use Redis or platform-provided state for
multi-replica production deployments.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.errors import GraphRecursionError
from langgraph.prebuilt import create_react_agent
from openai import APIError, RateLimitError
from pydantic import BaseModel, Field

from sdlc_data import DEFAULT_BRANCH, DEFAULT_REPOSITORY_URL
from system_prompt import SYSTEM_PROMPT
from tools import LANGCHAIN_TOOLS, run_mocked_sdlc_analysis

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("sdlc-copilot")

OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")
MAX_SESSION_MESSAGES = 40

FRIENDLY_FALLBACK = (
    "I could not complete the SDLC analysis right now. "
    "Please retry in a moment, or check the LLM/gateway configuration."
)

SESSIONS: dict[str, list[BaseMessage]] = {}
SESSION_LOCKS: dict[str, threading.Lock] = defaultdict(threading.Lock)

_agent = None


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message for the agent.")
    session_id: str = Field(..., description="Client-provided conversation/session id.")
    context: dict[str, Any] | None = Field(
        default=None,
        description="Optional WSO2 Agent Manager context payload.",
    )


class ChatResponse(BaseModel):
    response: str


class TriggerRequest(BaseModel):
    repository_url: str = Field(
        default=DEFAULT_REPOSITORY_URL,
        description="Repository URL or mocked repository name.",
    )
    branch: str = Field(
        default=DEFAULT_BRANCH,
        description="Branch to analyze.",
    )
    analysis_type: str = Field(
        default="release_readiness",
        description="release_readiness, pr_review, or security_scan.",
    )
    change_summary: str | None = Field(
        default=(
            "Demo trigger: analyze the current branch for release readiness, "
            "test gaps, security risk, and CI/CD confidence."
        ),
        description="Optional change summary to include in the analysis.",
    )
    use_llm: bool = Field(
        default=True,
        description=(
            "When true, invoke the LangGraph agent. When false, return deterministic "
            "mocked analysis without an LLM call."
        ),
    )


class TriggerResponse(BaseModel):
    analysis_id: str
    analysis_type: str
    response: str


def _resolve_llm_config() -> dict[str, Any]:
    """Resolve LLM credentials for BYO and WSO2 Agent Manager governed modes.

    Governed mode:
        OPENAI_URL is present.
        OPENAI_API_KEY is sent to the gateway as API-Key.
        Authorization is blanked so the OpenAI SDK bearer token is not used.

    BYO mode:
        OPENAI_URL is absent.
        OPENAI_API_KEY_DEFAULT is used directly with OpenAI.
    """

    base_url = os.getenv("OPENAI_URL")

    if base_url:
        return {
            "base_url": base_url,
            "api_key": "unused",
            "default_headers": {
                "API-Key": os.getenv("OPENAI_API_KEY", ""),
                "Authorization": "",
            },
        }

    return {"api_key": os.getenv("OPENAI_API_KEY_DEFAULT")}


def _get_agent():
    """Lazy-create the LangGraph ReAct agent.

    Laziness lets /health and unit tests import the module without requiring
    OpenAI credentials.
    """

    global _agent

    if _agent is None:
        llm = ChatOpenAI(model=OPENAI_MODEL, **_resolve_llm_config())
        _agent = create_react_agent(
            llm,
            tools=LANGCHAIN_TOOLS,
            prompt=SYSTEM_PROMPT,
        )

    return _agent


def _ready_payload() -> dict[str, Any]:
    return {
        "ok": True,
        "name": "sdlc-copilot-agent",
        "model": OPENAI_MODEL,
        "governed": bool(os.environ.get("OPENAI_URL")),
        "port": 8000,
        "llm_env": {
            "OPENAI_URL_set": bool(os.environ.get("OPENAI_URL")),
            "OPENAI_API_KEY_set": bool(os.environ.get("OPENAI_API_KEY")),
            "OPENAI_API_KEY_DEFAULT_set": bool(os.environ.get("OPENAI_API_KEY_DEFAULT")),
        },
        "endpoints": {
            "chat": "POST /chat",
            "trigger": "POST /trigger",
            "health": "GET /health",
        },
    }

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Emit a recognizable readiness line for platform logs."""

    log.info("READY %s", json.dumps(_ready_payload()))
    yield


app = FastAPI(
    title="SDLC Copilot Agent",
    description="WSO2 Agent Manager demo agent for software development lifecycle workflows.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    allow_credentials=False,
)


@app.get("/health")
def health() -> dict[str, Any]:
    return _ready_payload()


def _truncate(history: list[BaseMessage]) -> list[BaseMessage]:
    """Keep recent messages while avoiding orphaned ToolMessage entries."""

    if len(history) <= MAX_SESSION_MESSAGES:
        return history

    cut = len(history) - MAX_SESSION_MESSAGES

    while cut < len(history) and isinstance(history[cut], ToolMessage):
        cut += 1

    return history[cut:]


def _final_text(messages: list[BaseMessage]) -> str:
    """Return the last AIMessage text from a LangGraph response."""

    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            content = msg.content

            if isinstance(content, str):
                return content.strip()

            if isinstance(content, list):
                parts = [
                    block.get("text", "") if isinstance(block, dict) else str(block)
                    for block in content
                ]
                return "".join(parts).strip()

    return ""


def _invoke_agent(
    *,
    session_id: str,
    message: str,
    context: dict[str, Any] | None = None,
    persist_session: bool = True,
) -> str:
    started = time.perf_counter()

    if not message.strip():
        return "Tell me what SDLC workflow you want to analyze."

    sid = session_id or "_anonymous_"

    with SESSION_LOCKS[sid]:
        history = SESSIONS.get(sid, [])
        history = history + [HumanMessage(content=message)]

        if context:
            log.info("session=%s context=%s", sid, json.dumps(context)[:500])

        try:
            result = _get_agent().invoke(
                {"messages": history},
                config={
                    "configurable": {"thread_id": sid},
                    "metadata": {"session_id": sid},
                    "recursion_limit": 20,
                },
            )
            history = result["messages"]
            reply = _final_text(history) or FRIENDLY_FALLBACK

        except GraphRecursionError:
            log.warning("session=%s langgraph recursion limit exceeded", sid)
            reply = (
                "The analysis loop reached its limit. "
                "Please narrow the request to release readiness, PR review, security, or CI/CD."
            )

        except RateLimitError:
            log.warning("session=%s openai rate limit", sid)
            reply = FRIENDLY_FALLBACK

        except APIError as exc:
            log.warning("session=%s openai api error: %s", sid, exc)
            reply = FRIENDLY_FALLBACK

        except Exception as exc:  # pragma: no cover - defensive runtime path
            log.exception("session=%s unhandled error: %s", sid, exc)
            reply = FRIENDLY_FALLBACK

        if persist_session:
            SESSIONS[sid] = _truncate(history)

        log.info(
            "session=%s reply_chars=%d elapsed_ms=%d",
            sid,
            len(reply),
            int((time.perf_counter() - started) * 1000),
        )

    return reply


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    """Interactive chat endpoint."""

    reply = _invoke_agent(
        session_id=req.session_id,
        message=req.message,
        context=req.context,
        persist_session=True,
    )
    return ChatResponse(response=reply)


def _format_deterministic_trigger_response(analysis: dict[str, Any]) -> str:
    findings = analysis["quality"]["findings"]
    security = analysis["security"]
    ci_cd = analysis["ci_cd"]

    top_findings = findings[:3]
    finding_lines = "\n".join(
        (
            f"- {item['severity'].upper()}: {item['title']} "
            f"({item['category']}) — {item['recommendation']}"
        )
        for item in top_findings
    )

    action_lines = "\n".join(f"- {action}" for action in analysis["top_actions"])

    return f"""Decision: {analysis["decision"].upper()} with {analysis["confidence"]} confidence.

Mocked SDLC analysis `{analysis["analysis_id"]}` for `{analysis["repository"]["display_name"]}` on branch `{analysis["branch"]}`.

Summary:
{analysis["executive_summary"]}

Key findings:
{finding_lines}

CI/CD signal:
- Last build: {ci_cd["pipeline"]["last_build_status"]}
- Flaky tests in last 7 days: {ci_cd["pipeline"]["flaky_tests_last_7_days"]}
- Failed deployments in last 30 days: {ci_cd["pipeline"]["failed_deployments_last_30_days"]}

Security signal:
- Risk: {security["risk"]}
- Critical vulnerabilities: {security["summary"]["critical_vulnerabilities"]}
- High vulnerabilities: {security["summary"]["high_vulnerabilities"]}
- Secret leaks: {security["summary"]["secret_leaks"]}

Recommended next actions:
{action_lines}
"""


@app.post("/trigger", response_model=TriggerResponse)
def trigger(req: TriggerRequest) -> TriggerResponse:
    """Non-interactive trigger endpoint.

    This endpoint is intended for demos where an external system triggers an SDLC
    analysis and receives a completed answer without a back-and-forth chat.
    """

    deterministic_analysis = run_mocked_sdlc_analysis(
        repository_url=req.repository_url,
        branch=req.branch,
        analysis_type=req.analysis_type,
        change_summary=req.change_summary,
    )

    if not req.use_llm:
        return TriggerResponse(
            analysis_id=deterministic_analysis["analysis_id"],
            analysis_type=deterministic_analysis["analysis_type"],
            response=_format_deterministic_trigger_response(deterministic_analysis),
        )

    trigger_message = f"""
Run a one-shot mocked SDLC analysis.

Repository URL: {req.repository_url}
Branch: {req.branch}
Analysis type: {req.analysis_type}
Change summary: {req.change_summary}

Instructions:
- Call run_mocked_sdlc_analysis exactly once.
- Return an executive-ready answer.
- Include decision, confidence, key findings, security signal, CI/CD signal, and recommended next actions.
- Mention that this is a mocked demo analysis.
"""

    reply = _invoke_agent(
        session_id=f"trigger-{uuid.uuid4()}",
        message=trigger_message,
        context={
            "endpoint": "/trigger",
            "analysis_id": deterministic_analysis["analysis_id"],
            "analysis_type": req.analysis_type,
        },
        persist_session=False,
    )

    return TriggerResponse(
        analysis_id=deterministic_analysis["analysis_id"],
        analysis_type=deterministic_analysis["analysis_type"],
        response=reply,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("agent:app", host="0.0.0.0", port=8000, reload=False)