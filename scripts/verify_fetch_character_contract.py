from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "app"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(APP_DIR))

import nexon  # noqa: E402
from app.calc import API_OPTIONAL_SECTIONS, API_REQUIRED_SECTIONS  # noqa: E402
from scripts.verify_calculation import (  # noqa: E402
    recommendation_evidence_failures,
    sample_raw,
    single_metric_failures,
)


SAMPLE_RAW = sample_raw("레테", "INT", "마력", "INT : +3%")
PATH_TO_SECTION = {path: key for key, path in nexon.ENDPOINTS.items()}


def install_fake_request(fail_sections: set[str]) -> Callable[[str, dict[str, Any], int], dict[str, Any]]:
    def fake_request_json(path: str, params: dict[str, Any], retries: int = 3) -> dict[str, Any]:
        if path == "/id":
            return {"ocid": "sample-ocid"}

        if path == "/character/skill":
            section = f"skill{params.get('character_skill_grade')}"
        else:
            section = PATH_TO_SECTION.get(path, "")

        if section in fail_sections:
            raise nexon.NexonApiError(f"forced failure for {section}")

        if section in SAMPLE_RAW:
            return SAMPLE_RAW[section]
        return {}

    return fake_request_json


def with_fake_nexon(
    fail_sections: set[str],
    callback: Callable[[], None],
) -> None:
    original_request = nexon.request_json
    original_sleep = nexon.time.sleep
    try:
        nexon._CACHE.clear()  # pylint: disable=protected-access
        nexon.request_json = install_fake_request(fail_sections)  # type: ignore[assignment]
        nexon.time.sleep = lambda _seconds: None  # type: ignore[assignment]
        callback()
    finally:
        nexon.request_json = original_request  # type: ignore[assignment]
        nexon.time.sleep = original_sleep  # type: ignore[assignment]
        nexon._CACHE.clear()  # pylint: disable=protected-access


def assert_required_failures_raise() -> None:
    failures: list[str] = []
    for section in API_REQUIRED_SECTIONS:
        def run(section: str = section) -> None:
            try:
                nexon.fetch_character("레테샘플", "2026-06-21")
            except nexon.NexonApiError as exc:
                if section not in str(exc):
                    failures.append(f"{section}: raised error does not mention failed section: {exc}")
            else:
                failures.append(f"{section}: fetch_character returned a view for missing required API")

        with_fake_nexon({section}, run)

    if failures:
        raise AssertionError("\n".join(failures))


def assert_optional_failures_return_diagnostic_view() -> None:
    optional_failures = set(API_OPTIONAL_SECTIONS)

    def run() -> None:
        view = nexon.fetch_character("레테샘플", "2026-06-21")
        quality = view.get("apiDataQuality") or {}
        primary = view.get("primaryMetric") or {}
        summary = view.get("summary") or {}
        plan = view.get("itemUpgradePlan") or {}
        boss_board = view.get("bossBoard") or []
        readiness = view.get("readinessAudit") or {}
        problems: list[str] = []

        if quality.get("status") != "warning":
            problems.append(f"optional failure: API quality status is {quality.get('status')!r}")
        if quality.get("missingRequiredSections"):
            problems.append(f"optional failure: required sections missing {quality.get('missingRequiredSections')}")
        if set(quality.get("warningSections") or []) != optional_failures:
            problems.append("optional failure: warning sections do not match optional sections")
        if not optional_failures.issubset(set(quality.get("missingOptionalSections") or [])):
            problems.append("optional failure: missing optional sections incomplete")
        if primary.get("id") != "unifiedConverted380":
            problems.append("optional failure: primary metric id drifted")
        if primary.get("value") != summary.get("unifiedConverted380"):
            problems.append("optional failure: primary metric does not match summary")
        if primary.get("value") != plan.get("currentConverted"):
            problems.append("optional failure: primary metric does not match item plan")
        if boss_board and primary.get("value") != boss_board[0].get("currentConverted"):
            problems.append("optional failure: primary metric does not match boss board")
        problems.extend(single_metric_failures(view, "optional failure"))
        problems.extend(recommendation_evidence_failures(plan, "optional failure"))
        if not plan.get("top"):
            problems.append("optional failure: item recommendations disappeared")
        if (plan.get("reliability") or {}).get("status") != "caution":
            problems.append("optional failure: item plan reliability is not caution")
        if readiness.get("status") not in {"caution", "diagnostic"}:
            problems.append(f"optional failure: readiness status is {readiness.get('status')!r}")
        if problems:
            raise AssertionError("\n".join(problems))

    with_fake_nexon(optional_failures, run)


def main() -> None:
    assert_required_failures_raise()
    assert_optional_failures_return_diagnostic_view()
    print("OK: fetch_character required/optional API failure contract verified")


if __name__ == "__main__":
    main()
