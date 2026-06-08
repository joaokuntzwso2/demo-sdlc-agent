"""Mocked SDLC data used by the software-development-lifecycle demo agent.

This file is the single source of truth for deterministic demo data.
Tools should import from here rather than hardcoding their own findings.
"""

from __future__ import annotations

AGENT_NAME = "SDLC Copilot"
DEFAULT_REPOSITORY_URL = "https://github.com/acme-payments/checkout-service"
DEFAULT_BRANCH = "main"

REPOSITORIES: dict[str, dict] = {
    "checkout-service": {
        "display_name": "checkout-service",
        "repository_url": "https://github.com/acme-payments/checkout-service",
        "default_branch": "main",
        "domain": "payments",
        "owner_team": "Payments Platform",
        "runtime": "Python 3.11",
        "framework": "FastAPI",
        "deployment_target": "Kubernetes",
        "services": [
            "checkout-api",
            "payment-orchestrator",
            "receipt-worker",
        ],
        "critical_paths": [
            "payment authorization",
            "order confirmation",
            "receipt generation",
        ],
        "recent_changes": [
            "Added retry logic around payment-provider timeouts.",
            "Changed receipt-worker queue visibility timeout from 30s to 90s.",
            "Introduced feature flag `new_card_tokenizer`.",
        ],
        "quality_metrics": {
            "unit_test_coverage_percent": 81,
            "integration_test_coverage_percent": 64,
            "mutation_score_percent": 58,
            "lint_errors": 0,
            "type_check_errors": 3,
            "duplicated_code_percent": 4.2,
            "cyclomatic_hotspots": 2,
        },
        "pipeline": {
            "last_build_status": "passed",
            "last_build_duration_seconds": 412,
            "flaky_tests_last_7_days": 2,
            "failed_deployments_last_30_days": 1,
            "mean_time_to_restore_minutes": 42,
        },
        "security": {
            "critical_vulnerabilities": 0,
            "high_vulnerabilities": 1,
            "medium_vulnerabilities": 4,
            "secret_leaks": 0,
            "stale_dependencies": [
                "httpx 0.24.x",
                "pyjwt 2.6.x",
            ],
        },
        "operational": {
            "p95_latency_ms": 228,
            "error_rate_percent": 0.18,
            "slo_target_percent": 99.9,
            "current_availability_percent": 99.94,
        },
    },
    "inventory-service": {
        "display_name": "inventory-service",
        "repository_url": "https://github.com/acme-retail/inventory-service",
        "default_branch": "main",
        "domain": "retail inventory",
        "owner_team": "Supply Chain Engineering",
        "runtime": "Java 21",
        "framework": "Spring Boot",
        "deployment_target": "Kubernetes",
        "services": [
            "inventory-api",
            "stock-reconciliation-job",
            "warehouse-sync-consumer",
        ],
        "critical_paths": [
            "stock reservation",
            "warehouse sync",
            "low-stock notification",
        ],
        "recent_changes": [
            "Migrated stock reconciliation job to batched writes.",
            "Added warehouse-level stock projection endpoint.",
            "Changed Redis cache TTL from 60s to 300s.",
        ],
        "quality_metrics": {
            "unit_test_coverage_percent": 74,
            "integration_test_coverage_percent": 51,
            "mutation_score_percent": 46,
            "lint_errors": 4,
            "type_check_errors": 0,
            "duplicated_code_percent": 7.8,
            "cyclomatic_hotspots": 5,
        },
        "pipeline": {
            "last_build_status": "passed",
            "last_build_duration_seconds": 689,
            "flaky_tests_last_7_days": 5,
            "failed_deployments_last_30_days": 2,
            "mean_time_to_restore_minutes": 76,
        },
        "security": {
            "critical_vulnerabilities": 0,
            "high_vulnerabilities": 2,
            "medium_vulnerabilities": 7,
            "secret_leaks": 0,
            "stale_dependencies": [
                "spring-security 6.1.x",
                "postgresql-driver 42.5.x",
            ],
        },
        "operational": {
            "p95_latency_ms": 412,
            "error_rate_percent": 0.36,
            "slo_target_percent": 99.5,
            "current_availability_percent": 99.61,
        },
    },
}

FINDINGS: dict[str, list[dict]] = {
    "checkout-service": [
        {
            "id": "SDLC-001",
            "severity": "high",
            "category": "reliability",
            "title": "Payment retry path is not covered by integration tests",
            "location": "tests/integration/test_payment_provider.py",
            "evidence": "Retry logic was added, but the timeout and duplicate-authorization cases are not covered.",
            "recommendation": "Add provider-timeout and idempotency integration tests before production rollout.",
        },
        {
            "id": "SDLC-002",
            "severity": "medium",
            "category": "maintainability",
            "title": "Payment orchestration function exceeds complexity threshold",
            "location": "checkout/payment_orchestrator.py",
            "evidence": "Cyclomatic complexity is 18; threshold is 12.",
            "recommendation": "Split authorization, capture, and rollback decisions into separate units.",
        },
        {
            "id": "SDLC-003",
            "severity": "medium",
            "category": "security",
            "title": "JWT dependency is behind the approved baseline",
            "location": "requirements.txt",
            "evidence": "pyjwt 2.6.x is listed as stale in the dependency inventory.",
            "recommendation": "Upgrade to the organization-approved PyJWT baseline and run auth regression tests.",
        },
        {
            "id": "SDLC-004",
            "severity": "low",
            "category": "delivery",
            "title": "Two flaky tests observed in the last seven days",
            "location": "CI pipeline history",
            "evidence": "Flakes occurred in receipt-worker queue timing tests.",
            "recommendation": "Stabilize async queue tests using deterministic clock or explicit polling timeout.",
        },
    ],
    "inventory-service": [
        {
            "id": "SDLC-101",
            "severity": "high",
            "category": "quality",
            "title": "Integration coverage is below release threshold",
            "location": "build quality gate",
            "evidence": "Integration coverage is 51%; target is 60%.",
            "recommendation": "Add warehouse sync and stock reservation integration tests.",
        },
        {
            "id": "SDLC-102",
            "severity": "high",
            "category": "security",
            "title": "Two high-severity dependency vulnerabilities",
            "location": "dependency scan",
            "evidence": "spring-security and postgresql-driver are behind approved baselines.",
            "recommendation": "Upgrade dependencies and rerun SCA plus authentication regression checks.",
        },
        {
            "id": "SDLC-103",
            "severity": "medium",
            "category": "reliability",
            "title": "Warehouse sync consumer has elevated error rate",
            "location": "warehouse-sync-consumer",
            "evidence": "Current service error rate is 0.36%, above the desired internal target of 0.25%.",
            "recommendation": "Add retry budget monitoring and validate dead-letter handling before release.",
        },
        {
            "id": "SDLC-104",
            "severity": "medium",
            "category": "maintainability",
            "title": "Five complexity hotspots detected",
            "location": "src/main/java/com/acme/inventory",
            "evidence": "Static analysis found five methods above complexity threshold.",
            "recommendation": "Refactor stock projection and reconciliation decision branches.",
        },
    ],
}

ANALYSIS_POLICIES = {
    "release_readiness": {
        "name": "Release readiness",
        "description": "Assess whether a repository is safe to release.",
        "pass_criteria": [
            "No critical security vulnerabilities.",
            "No untested high-risk code path in critical flows.",
            "CI is passing.",
            "Rollback or mitigation plan exists for medium/high risks.",
        ],
    },
    "pr_review": {
        "name": "Pull request review",
        "description": "Review a change for quality, test gaps, security, and operational risk.",
        "pass_criteria": [
            "Change is covered by meaningful tests.",
            "No obvious security regression.",
            "Operational blast radius is understood.",
            "Code complexity remains within agreed thresholds.",
        ],
    },
    "security_scan": {
        "name": "Security scan",
        "description": "Summarize security and dependency risk.",
        "pass_criteria": [
            "No critical vulnerabilities.",
            "High vulnerabilities have an owner and target date.",
            "No detected secret leaks.",
            "Authentication and authorization paths remain covered by tests.",
        ],
    },
}