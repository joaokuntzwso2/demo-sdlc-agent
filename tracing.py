"""Optional OpenTelemetry tracing initialization for WSO2 Agent Manager.

This file is intentionally safe:
- No-op locally unless AMP_OTEL_ENDPOINT and AMP_AGENT_API_KEY are present.
- Never prevents the agent from booting if tracing initialization fails.
- Should be imported before LangChain/LangGraph symbols load.
"""

from __future__ import annotations

import os
import sys


def _init() -> None:
    endpoint = os.environ.get("AMP_OTEL_ENDPOINT")
    api_key = os.environ.get("AMP_AGENT_API_KEY")

    if not endpoint or not api_key:
        return

    os.environ.setdefault(
        "TRACELOOP_TRACE_CONTENT",
        os.environ.get("AMP_TRACE_CONTENT", "true"),
    )
    os.environ.setdefault("TRACELOOP_METRICS_ENABLED", "false")
    os.environ.setdefault("OTEL_EXPORTER_OTLP_INSECURE", "true")

    resource_attributes: dict[str, str] = {
        "service.name": os.environ.get("AMP_AGENT_NAME", "sdlc-copilot-agent"),
    }

    if version := os.environ.get("AMP_AGENT_VERSION"):
        resource_attributes["agent-manager/agent-version"] = version

    try:
        from traceloop.sdk import Traceloop

        Traceloop.init(
            telemetry_enabled=False,
            api_endpoint=endpoint,
            headers={"x-amp-api-key": api_key},
            resource_attributes=resource_attributes,
        )
    except Exception as exc:  # pragma: no cover - defensive by design
        print(f"tracing: Traceloop.init failed: {exc}", file=sys.stderr)


_init()