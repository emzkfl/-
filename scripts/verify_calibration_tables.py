from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.calc import (  # noqa: E402
    CALIBRATION_EVIDENCE,
    KMS_JOB_NAMES,
    K_ATTACK,
    K_BOSS,
    K_COMBAT,
    K_CRIT_DAMAGE,
    K_CRIT_RATE,
    K_DAMAGE,
    K_FINAL,
    K_HP,
    K_IED,
    K_MAGIC,
    build_view_model,
    choose_attack_type,
    choose_main_stat,
    job_converted_multiplier,
    job_detail_rule,
)


MAX_SAMPLE_ERROR_PERCENT = 0.01
MAX_SPECIAL_SAMPLE_ERROR_PERCENT = 5.0
MAX_SPECIAL_AVERAGE_ERROR_PERCENT = 2.5


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
    if set(CALIBRATION_EVIDENCE) != set(KMS_JOB_NAMES):
        missing = sorted(set(KMS_JOB_NAMES) - set(CALIBRATION_EVIDENCE))
        extra = sorted(set(CALIBRATION_EVIDENCE) - set(KMS_JOB_NAMES))
        failures.append(f"embedded evidence job set mismatch missing={missing} extra={extra}")

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

        embedded = CALIBRATION_EVIDENCE.get(job)
        if not embedded:
            failures.append(f"{job}: embedded calibration evidence missing")
        elif abs(float(embedded.get("multiplier") or 0.0) - stored_multiplier) > 0.000001:
            failures.append(f"{job}: embedded multiplier drift {embedded.get('multiplier')} != {stored_multiplier}")

        raw = float(row.get("rawConverted") or 0.0)
        origin = float(row.get("originConverted") or 0.0)
        if embedded:
            if abs(float(embedded.get("rawConverted") or 0.0) - raw) > 0.001:
                failures.append(f"{job}: embedded raw drift {embedded.get('rawConverted')} != {raw}")
            if int(embedded.get("originConverted") or 0) != int(origin):
                failures.append(f"{job}: embedded origin drift {embedded.get('originConverted')} != {origin}")
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


def special_sample_raw(row: dict[str, Any]) -> dict[str, Any]:
    stats = [
        ("STR", row.get("STR")),
        ("DEX", row.get("DEX")),
        ("INT", row.get("INT")),
        ("LUK", row.get("LUK")),
        (K_HP, row.get("HP")),
        (K_ATTACK, row.get("attack")),
        (K_MAGIC, row.get("magic")),
        (K_DAMAGE, row.get("damage")),
        (K_BOSS, row.get("bossDamage")),
        (K_FINAL, row.get("finalDamage")),
        (K_IED, row.get("ied")),
        (K_CRIT_RATE, row.get("critRate")),
        (K_CRIT_DAMAGE, row.get("critDamage")),
        (K_COMBAT, row.get("originCombatPower")),
    ]
    return {
        "basic": {
            "character_name": row.get("name") or "special-sample",
            "world_name": "-",
            "character_class": row.get("class") or row.get("job") or "",
            "character_level": row.get("level") or 0,
        },
        "stat": {
            "final_stat": [
                {"stat_name": key, "stat_value": str(value)}
                for key, value in stats
                if value is not None
            ]
        },
        "itemEquipment": {"item_equipment": []},
    }


def assert_special_job_samples(data: dict[str, Any]) -> None:
    rows = data.get("rows") or []
    problems: list[str] = []
    if len(rows) < 40:
        problems.append(f"special-job-samples.json expected at least 40 rows, got {len(rows)}")

    errors = []
    jobs = set()
    for row in rows:
        job = str(row.get("job") or "")
        jobs.add(job)
        origin = float(row.get("originConverted") or 0.0)
        if origin <= 0:
            problems.append(f"{job}/{row.get('name')}: originConverted missing")
            continue
        view = build_view_model(special_sample_raw(row))
        primary = float(view["primaryMetric"]["value"])
        error = abs(primary - origin) / origin * 100
        errors.append(error)
        if error > MAX_SPECIAL_SAMPLE_ERROR_PERCENT:
            problems.append(
                f"{job}/{row.get('name')}: primaryMetric error {error:.3f}% "
                f"({primary:.0f} != {origin:.0f})"
            )

    if jobs != {"데몬어벤져", "제논"}:
        problems.append(f"special sample jobs drifted: {sorted(jobs)}")
    average_error = sum(errors) / len(errors) if errors else 0.0
    if average_error > MAX_SPECIAL_AVERAGE_ERROR_PERCENT:
        problems.append(
            f"special sample average error {average_error:.3f}% exceeds "
            f"{MAX_SPECIAL_AVERAGE_ERROR_PERCENT}%"
        )

    if problems:
        raise AssertionError("\n".join(problems))


def main() -> None:
    calibration = read_json(ROOT / "calibration-results.json")
    rankings = read_json(ROOT / "calibration-rankings.json")
    special_samples = read_json(ROOT / "special-job-samples.json")
    if calibration is None or rankings is None:
        print("SKIP: local calibration JSON files are not present")
        return

    assert_calibration_results(calibration)
    assert_ranking_samples(rankings)
    if special_samples is not None:
        assert_special_job_samples(special_samples)
    print(f"OK: calibration tables match {len(KMS_JOB_NAMES)} KMS jobs")


if __name__ == "__main__":
    main()
