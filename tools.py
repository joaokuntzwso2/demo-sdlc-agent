"""LangChain tools for the SDLC Copilot demo agent.

All tools are deterministic and mocked. They never call external systems and
never raise into the agent loop. This makes the demo stable while still showing
tool-calling, traces, and governed LLM behavior.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from langchain_core.tools import tool

from sdlc_data import (
    ANALYSIS_POLICIES,
    DEFAULT_BRANCH,
    DEFAULT_REPOSITORY_URL,
    FINDINGS,
    REPOSITORIES,
)

_REPO_NAME_RE = re.compile(r"/([^/]+?)(?:\.git)?/?$")


def _repo_key(repository_url: str | None) -> str:
    """Map a repository URL or loose name to one of the mocked repositories."""

    raw = (repository_url or DEFAULT_REPOSITORY_URL).strip()

    if not raw:
        return "checkout-service"

    match = _REPO_NAME_RE.search(raw)
    candidate = match.group(1) if match else raw
    candidate = candidate.strip().lower()

    if candidate in REPOSITORIES:
        return candidate

    # Helpful aliases for natural-language chat.
    aliases = {
        "checkout": "checkout-service",
        "payments": "checkout-service",
        "payment": "checkout-service",
        "inventory": "inventory-service",
        "stock": "inventory-service",
    }

    return aliases.get(candidate, "checkout-service")


def _analysis_id(repository_key: str, branch: str, analysis_type: str) -> str:
    digest = hashlib.sha256(
        f"{repository_key}:{branch}:{analysis_type}".encode("utf-8")
    ).hexdigest()
    return f"mock-{digest[:10]}"


def get_repository_snapshot(
    repository_url: str | None = None,
    branch: str | None = None,
) -> dict[str, Any]:
    """Return mocked repository, ownership, runtime, pipeline, and operational metadata.

    Use this when the user asks what the repository looks like, who owns it,
    what technology stack it uses, or what baseline metrics are available.

    Args:
        repository_url: Repository URL or name. Optional; defaults to the demo checkout service.
        branch: Git branch. Optional; defaults to main.
    """

    key = _repo_key(repository_url)
    repo = REPOSITORIES[key]
    selected_branch = branch or repo.get("default_branch") or DEFAULT_BRANCH

    return {
        "repository_key": key,
        "branch": selected_branch,
        "repository": repo,
    }


def run_static_quality_scan(
    repository_url: str | None = None,
    branch: str | None = None,
    category: str | None = None,
) -> dict[str, Any]:
    """Run a mocked static quality scan and return findings.

    Use this when the user asks about code quality, maintainability, test gaps,
    complexity, release blockers, or PR review findings.

    Args:
        repository_url: Repository URL or name. Optional.
        branch: Git branch. Optional.
        category: Optional category filter: reliability, maintainability, security,
            delivery, or quality.
    """

    key = _repo_key(repository_url)
    selected_branch = branch or REPOSITORIES[key]["default_branch"]
    all_findings = FINDINGS[key]

    if category:
        filtered = [
            finding
            for finding in all_findings
            if finding["category"].lower() == category.strip().lower()
        ]
    else:
        filtered = all_findings

    severity_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    sorted_findings = sorted(
        filtered,
        key=lambda item: severity_rank.get(item["severity"], 0),
        reverse=True,
    )

    return {
        "repository_key": key,
        "branch": selected_branch,
        "category_filter": category or "none",
        "findings": sorted_findings,
        "count": len(sorted_findings),
    }


def run_security_dependency_scan(
    repository_url: str | None = None,
    branch: str | None = None,
) -> dict[str, Any]:
    """Run a mocked dependency/security scan.

    Use this for security, dependency, CVE, secret, authentication, or
    authorization questions.

    Args:
        repository_url: Repository URL or name. Optional.
        branch: Git branch. Optional.
    """

    key = _repo_key(repository_url)
    repo = REPOSITORIES[key]
    selected_branch = branch or repo["default_branch"]
    security = repo["security"]
    security_findings = [
        finding for finding in FINDINGS[key] if finding["category"] == "security"
    ]

    if security["critical_vulnerabilities"] > 0:
        risk = "blocker"
    elif security["high_vulnerabilities"] > 0:
        risk = "high"
    elif security["medium_vulnerabilities"] > 0:
        risk = "medium"
    else:
        risk = "low"

    return {
        "repository_key": key,
        "branch": selected_branch,
        "risk": risk,
        "summary": security,
        "security_findings": security_findings,
        "recommended_gate": (
            "Do not release until critical/high items are owned."
            if risk in {"blocker", "high"}
            else "Release can proceed with normal monitoring."
        ),
    }


def get_ci_cd_health(
    repository_url: str | None = None,
    branch: str | None = None,
) -> dict[str, Any]:
    """Return mocked CI/CD and delivery health.

    Use this when the user asks about build health, deployment risk, flaky tests,
    rollback risk, or release confidence.

    Args:
        repository_url: Repository URL or name. Optional.
        branch: Git branch. Optional.
    """

    key = _repo_key(repository_url)
    repo = REPOSITORIES[key]
    selected_branch = branch or repo["default_branch"]
    pipeline = repo["pipeline"]

    risk_notes: list[str] = []

    if pipeline["last_build_status"] != "passed":
        risk_notes.append("Last build did not pass.")
    if pipeline["flaky_tests_last_7_days"] >= 3:
        risk_notes.append("Flaky test count is elevated.")
    elif pipeline["flaky_tests_last_7_days"] > 0:
        risk_notes.append("Some flaky tests were observed.")
    if pipeline["failed_deployments_last_30_days"] > 1:
        risk_notes.append("Deployment failure count is elevated.")

    if not risk_notes:
        risk_notes.append("CI/CD signal is healthy.")

    return {
        "repository_key": key,
        "branch": selected_branch,
        "pipeline": pipeline,
        "risk_notes": risk_notes,
    }


def run_mocked_sdlc_analysis(
    repository_url: str | None = None,
    branch: str | None = None,
    analysis_type: str | None = None,
    change_summary: str | None = None,
) -> dict[str, Any]:
    """Run the full mocked SDLC analysis used by the non-interactive trigger endpoint.

    Use this when the request is a one-shot trigger, release-readiness check,
    pull-request review, or broad SDLC analysis.

    Args:
        repository_url: Repository URL or name. Optional.
        branch: Git branch. Optional.
        analysis_type: One of release_readiness, pr_review, or security_scan.
        change_summary: Optional description of the change being analyzed.
    """

    requested_type = (analysis_type or "release_readiness").strip().lower()
    if requested_type not in ANALYSIS_POLICIES:
        requested_type = "release_readiness"

    key = _repo_key(repository_url)
    repo = REPOSITORIES[key]
    selected_branch = branch or repo["default_branch"]

    quality = run_static_quality_scan(repo["repository_url"], selected_branch)
    security = run_security_dependency_scan(repo["repository_url"], selected_branch)
    ci_cd = get_ci_cd_health(repo["repository_url"], selected_branch)
    snapshot = get_repository_snapshot(repo["repository_url"], selected_branch)

    findings = quality["findings"]
    high_or_worse = [
        finding
        for finding in findings
        if finding["severity"] in {"critical", "high"}
    ]

    if security["risk"] == "blocker":
        decision = "blocked"
        confidence = "low"
    elif high_or_worse:
        decision = "conditional"
        confidence = "medium"
    elif ci_cd["pipeline"]["last_build_status"] == "passed":
        decision = "ready"
        confidence = "high"
    else:
        decision = "conditional"
        confidence = "medium"

    top_actions = [
        finding["recommendation"]
        for finding in findings
        if finding["severity"] in {"critical", "high", "medium"}
    ][:4]

    if not top_actions:
        top_actions = ["Proceed with release using standard monitoring and rollback checks."]

    return {
        "analysis_id": _analysis_id(key, selected_branch, requested_type),
        "analysis_type": requested_type,
        "policy": ANALYSIS_POLICIES[requested_type],
        "repository_key": key,
        "repository": snapshot["repository"],
        "branch": selected_branch,
        "change_summary": change_summary or "No change summary provided.",
        "decision": decision,
        "confidence": confidence,
        "quality": quality,
        "security": security,
        "ci_cd": ci_cd,
        "top_actions": top_actions,
        "executive_summary": (
            f"{repo['display_name']} is {decision} for {requested_type}. "
            f"The strongest signals are {len(high_or_worse)} high-or-worse finding(s), "
            f"CI status '{ci_cd['pipeline']['last_build_status']}', and security risk "
            f"'{security['risk']}'."
        ),
    }


LANGCHAIN_TOOLS = [
    tool(get_repository_snapshot),
    tool(run_static_quality_scan),
    tool(run_security_dependency_scan),
    tool(get_ci_cd_health),
    tool(run_mocked_sdlc_analysis),
]

__all__ = [
    "LANGCHAIN_TOOLS",
    "get_repository_snapshot",
    "run_static_quality_scan",
    "run_security_dependency_scan",
    "get_ci_cd_health",
    "run_mocked_sdlc_analysis",
]