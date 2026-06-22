from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.calc import (  # noqa: E402
    KMS_JOB_NAMES,
    choose_attack_type,
    choose_main_stat,
    job_converted_multiplier,
    job_detail_rule,
)


MAX_SAMPLE_ERROR_PERCENT = 0.01


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def assert_calibration_results(data: dict[str, Any]) -> None:
    jobs = data.get("jobs") or {}
    failures: list[str] = []

    if data.get("errors"):
        failures.append(f"calibration-results.json has errors: {data['errors']}")
    if set(jobs) != set(KMS_JOB_NAMES):
        missing = sorted(set(KMS_JOB_NAMES) - set(jobs))
        extra = sorted(set(jobs) - set(KMS_JOB_NAMES))
        failures.append(f"job set mismatch missing={missing} extra={extra}")

    for job in KMS_JOB_NAMES:
        row = jobs.get(job) or {}
        if row.get("status") != "ok":
            failures.append(f"{job}: status is {row.get('status')!r}")
        if row.get("confidence") != "high":
            failures.append(f"{job}: confidence is {row.get('confidence')!r}")
        if not job_detail_rule(job):
            failures.append(f"{job}: detail rule missing")
        if row.get("mainStat") and row["mainStat"] != choose_main_stat({}, job):
            failures.append(f"{job}: main stat drift {row['mainStat']} != {choose_main_stat({}, job)}")
        if row.get("attackType") and row["attackType"] != choose_attack_type({}, job):
            failures.append(f"{job}: attack type drift {row['attackType']} != {choose_attack_type({}, job)}")

        stored_multiplier = float(row.get("multiplier") or 0.0)
        current_multiplier = job_converted_multiplier(job)
        if abs(stored_multiplier - current_multiplier) > 0.000001:
            failures.append(f"{job}: multiplier drift {stored_multiplier} != {current_multiplier}")

        raw = float(row.get("rawConverted") or 0.0)
        origin = float(row.get("originConverted") or 0.0)
        if raw <= 0 or origin <= 0 or stored_multiplier <= 0:
            failures.append(f"{job}: missing raw/origin/multiplier calibration values")
            continue
        estimated = raw * stored_multiplier
        error_percent = abs(estimated - origin) / origin * 100
        if error_percent > MAX_SAMPLE_ERROR_PERCENT:
            failures.append(f"{job}: sample error {error_percent:.4f}% exceeds {MAX_SAMPLE_ERROR_PERCENT}%")

    if failures:
        raise AssertionError("\n".join(failures))


def assert_ranking_samples(data: dict[str, Any]) -> None:
    samples = data.get("samples") or {}
    failures = data.get("failures") or []
    problems: list[str] = []

    if failures:
        problems.append(f"calibration-rankings.json has failures: {failures[:3]}")
    if set(samples) != set(KMS_JOB_NAMES):
        missing = sorted(set(KMS_JOB_NAMES) - set(samples))
        extra = sorted(set(samples) - set(KMS_JOB_NAMES))
        problems.append(f"ranking job set mismatch missing={missing} extra={extra}")

    for job in KMS_JOB_NAMES:
        rows = samples.get(job) or []
        if len(rows) < 30:
            problems.append(f"{job}: expected at least 30 ranking samples, got {len(rows)}")
        if rows and rows[0].get("job") != job:
            problems.append(f"{job}: first ranking sample job is {rows[0].get('job')!r}")

    if problems:
        raise AssertionError("\n".join(problems))


def main() -> None:
    calibration = read_json(ROOT / "calibration-results.json")
    rankings = read_json(ROOT / "calibration-rankings.json")
    if calibration is None or rankings is None:
        print("SKIP: local calibration JSON files are not present")
        return

    assert_calibration_results(calibration)
    assert_ranking_samples(rankings)
    print(f"OK: calibration tables match {len(KMS_JOB_NAMES)} KMS jobs")


if __name__ == "__main__":
    main()
