from __future__ import annotations

from tools import (
    get_ci_cd_health,
    get_repository_snapshot,
    run_mocked_sdlc_analysis,
    run_security_dependency_scan,
    run_static_quality_scan,
)


def test_repository_snapshot_defaults_to_checkout_service() -> None:
    result = get_repository_snapshot()

    assert result["repository_key"] == "checkout-service"
    assert result["branch"] == "main"
    assert result["repository"]["display_name"] == "checkout-service"


def test_repository_snapshot_maps_inventory_url() -> None:
    result = get_repository_snapshot("https://github.com/acme-retail/inventory-service")

    assert result["repository_key"] == "inventory-service"
    assert result["repository"]["display_name"] == "inventory-service"


def test_static_quality_scan_returns_findings() -> None:
    result = run_static_quality_scan("checkout-service")

    assert result["count"] >= 1
    assert result["findings"][0]["severity"] in {"critical", "high", "medium", "low"}


def test_static_quality_scan_filters_category() -> None:
    result = run_static_quality_scan("checkout-service", category="security")

    assert result["count"] == 1
    assert result["findings"][0]["category"] == "security"


def test_security_dependency_scan_has_risk() -> None:
    result = run_security_dependency_scan("checkout-service")

    assert result["risk"] in {"blocker", "high", "medium", "low"}
    assert "summary" in result
    assert "security_findings" in result


def test_ci_cd_health_has_pipeline() -> None:
    result = get_ci_cd_health("checkout-service")

    assert result["pipeline"]["last_build_status"] == "passed"
    assert result["risk_notes"]


def test_full_mocked_sdlc_analysis_shape() -> None:
    result = run_mocked_sdlc_analysis(
        repository_url="checkout-service",
        branch="main",
        analysis_type="release_readiness",
        change_summary="Test change",
    )

    assert result["analysis_id"].startswith("mock-")
    assert result["decision"] in {"ready", "conditional", "blocked"}
    assert result["confidence"] in {"high", "medium", "low"}
    assert result["top_actions"]