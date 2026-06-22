from __future__ import annotations

import json
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "app"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(APP_DIR))

import server  # noqa: E402


def request_json(
    base_url: str,
    path: str,
    method: str = "GET",
    payload: Any | None = None,
) -> tuple[int, dict[str, Any]]:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(f"{base_url}{path}", data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=5) as response:
            body = json.loads(response.read().decode("utf-8"))
            return response.status, body
    except HTTPError as exc:
        body = json.loads(exc.read().decode("utf-8"))
        return exc.code, body


def assert_server_http_contract() -> None:
    calls: list[dict[str, Any]] = []

    def fake_default_date() -> str:
        return "2026-06-21"

    def fake_fetch_character(character_name: str, date: str | None = None) -> dict[str, Any]:
        calls.append({"characterName": character_name, "date": date})
        if not character_name:
            raise server.NexonApiError("닉네임을 입력해주세요.")
        return {
            "date": date,
            "basic": {"character_name": character_name},
            "primaryMetric": {"id": "unifiedConverted380", "value": 123456},
            "goalContract": {
                "version": "single_metric_repair_v1",
                "metricId": "unifiedConverted380",
                "metricValue": 123456,
                "canCompareUsers": True,
                "canJudgeBosses": True,
                "canRecommendItems": True,
            },
            "unifiedRepairAudit": {
                "version": "unified_repair_audit_v1",
                "metric": "unifiedConverted380",
                "metricValue": 123456,
                "allPassed": True,
            },
            "summary": {"unifiedConverted380": 123456},
            "itemUpgradePlan": {
                "currentConverted": 123456,
                "repairFocus": {"slot": "무기", "description": "무기 잠재 보강"},
            },
            "bossBoard": [{"currentConverted": 123456}],
        }

    original_default_date = server.default_date
    original_fetch_character = server.fetch_character
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)

    try:
        server.default_date = fake_default_date  # type: ignore[assignment]
        server.fetch_character = fake_fetch_character  # type: ignore[assignment]
        thread.start()
        base_url = f"http://127.0.0.1:{httpd.server_port}"

        health_status, health = request_json(base_url, "/api/health")
        if health_status != 200 or health != {"ok": True, "defaultDate": "2026-06-21"}:
            raise AssertionError(f"health response mismatch: {health_status} {health}")

        formula_status, formulas = request_json(base_url, "/api/formulas")
        if formula_status != 200:
            raise AssertionError(f"formula response status mismatch: {formula_status} {formulas}")
        if formulas.get("metricId") != "unifiedConverted380":
            raise AssertionError(f"formula response metric id mismatch: {formulas}")
        if formulas.get("jobCount", 0) < 48:
            raise AssertionError(f"formula response job count too small: {formulas.get('jobCount')}")
        if "레테" not in (formulas.get("knownJobs") or []):
            raise AssertionError("formula response does not expose 레테")
        coverage = formulas.get("coverage") or {}
        if coverage.get("targetJobs") != formulas.get("jobCount"):
            raise AssertionError(f"formula coverage target mismatch: {coverage}")
        if coverage.get("missingDetailJobs") or coverage.get("missingMultiplierJobs") or coverage.get("missingCombatJobs"):
            raise AssertionError(f"formula coverage has missing jobs: {coverage}")
        lete = next((row for row in formulas.get("jobs") or [] if row.get("job") == "레테"), None)
        if not lete or lete.get("mainStat") != "INT" or lete.get("attackType") != "마력":
            raise AssertionError(f"formula response 레테 row mismatch: {lete}")
        if float(lete.get("weaponConstant") or 0) <= 0 or float(lete.get("jobConvertedMultiplier") or 0) <= 0:
            raise AssertionError(f"formula response 레테 coefficients missing: {lete}")
        if "damageFactor" not in (formulas.get("formulas") or {}):
            raise AssertionError(f"formula response calculation formula missing: {formulas}")
        if formulas.get("bossRuleCount", 0) <= 0 or not formulas.get("bossRules"):
            raise AssertionError(f"formula response boss rules missing: {formulas}")
        if "bossEffectiveMetric" not in (formulas.get("formulas") or {}):
            raise AssertionError(f"formula response boss effective formula missing: {formulas}")

        status, body = request_json(
            base_url,
            "/api/character",
            method="POST",
            payload={"characterName": "레테샘플", "date": "2026-06-21"},
        )
        if status != 200:
            raise AssertionError(f"character response status mismatch: {status} {body}")
        if body.get("primaryMetric", {}).get("id") != "unifiedConverted380":
            raise AssertionError(f"character response primary metric missing: {body}")
        if body.get("goalContract", {}).get("version") != "single_metric_repair_v1":
            raise AssertionError(f"character response goal contract missing: {body}")
        if body.get("goalContract", {}).get("metricValue") != body.get("primaryMetric", {}).get("value"):
            raise AssertionError(f"character response goal contract metric mismatch: {body}")
        if body.get("goalContract", {}).get("canJudgeBosses") is not True:
            raise AssertionError(f"character response goal contract boss flag missing: {body}")
        if body.get("unifiedRepairAudit", {}).get("version") != "unified_repair_audit_v1":
            raise AssertionError(f"character response unified repair audit missing: {body}")
        if body.get("unifiedRepairAudit", {}).get("metricValue") != body.get("primaryMetric", {}).get("value"):
            raise AssertionError(f"character response unified repair audit metric mismatch: {body}")
        if body.get("summary", {}).get("unifiedConverted380") != body.get("primaryMetric", {}).get("value"):
            raise AssertionError(f"character response single metric mismatch: {body}")
        if body.get("itemUpgradePlan", {}).get("currentConverted") != body.get("primaryMetric", {}).get("value"):
            raise AssertionError(f"character response repair plan metric mismatch: {body}")
        if calls != [{"characterName": "레테샘플", "date": "2026-06-21"}]:
            raise AssertionError(f"fetch_character call mismatch: {calls}")

        error_status, error = request_json(
            base_url,
            "/api/character",
            method="POST",
            payload={"characterName": ""},
        )
        if error_status != 400 or "error" not in error:
            raise AssertionError(f"empty name error mismatch: {error_status} {error}")

        not_found_status, not_found = request_json(
            base_url,
            "/api/missing",
            method="POST",
            payload={},
        )
        if not_found_status != 404 or not_found.get("error") != "not found":
            raise AssertionError(f"missing endpoint mismatch: {not_found_status} {not_found}")
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)
        server.default_date = original_default_date  # type: ignore[assignment]
        server.fetch_character = original_fetch_character  # type: ignore[assignment]


def main() -> None:
    assert_server_http_contract()
    print("OK: server HTTP API contract verified")


if __name__ == "__main__":
    main()
