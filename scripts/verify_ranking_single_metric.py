from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.calc import KMS_JOB_NAMES, build_view_model  # noqa: E402
from scripts.verify_calculation import single_metric_failures  # noqa: E402
from scripts.verify_calibration_tables import (  # noqa: E402
    MAX_RANKING_COMBAT_AVERAGE_ERROR_PERCENT,
    MAX_RANKING_COMBAT_ERROR_PERCENT,
    RANKING_COMBAT_ERROR_LIMITS,
    special_sample_raw,
)


def assert_ranking_single_metric() -> None:
    path = ROOT / "calibration-rankings.json"
    if not path.exists():
        print("SKIP: calibration-rankings.json is not present")
        return

    data = json.loads(path.read_text(encoding="utf-8"))
    samples = data.get("samples") or {}
    failures: list[str] = []

    if set(samples) != set(KMS_JOB_NAMES):
        missing = sorted(set(KMS_JOB_NAMES) - set(samples))
        extra = sorted(set(samples) - set(KMS_JOB_NAMES))
        failures.append(f"ranking sample job set mismatch missing={missing} extra={extra}")

    checked = 0
    for job in KMS_JOB_NAMES:
        rows = samples.get(job) or []
        errors: list[float] = []
        for row in rows[:30]:
            context = f"{job}/{row.get('name') or row.get('rank')}"
            origin = float(row.get("originConverted") or 0.0)
            if origin <= 0:
                failures.append(f"{context}: origin converted missing")
                continue

            view = build_view_model(special_sample_raw(row))
            primary = view.get("primaryMetric") or {}
            summary = view.get("summary") or {}
            converted = float(primary.get("value") or 0.0)
            model = str(summary.get("convertedModel") or "")

            if converted <= 0:
                failures.append(f"{context}: representative metric is zero")
            if "combat" not in model:
                failures.append(f"{context}: ranking fallback did not use combat model ({model})")
            if primary.get("id") != "unifiedConverted380":
                failures.append(f"{context}: primary metric id drifted")
            failures.extend(single_metric_failures(view, context))

            error = abs(converted - origin) / origin * 100
            errors.append(error)
            checked += 1

        if not errors:
            failures.append(f"{job}: no ranking rows checked")
            continue

        limits = RANKING_COMBAT_ERROR_LIMITS.get(
            job,
            {"max": MAX_RANKING_COMBAT_ERROR_PERCENT, "average": MAX_RANKING_COMBAT_AVERAGE_ERROR_PERCENT},
        )
        max_error = max(errors)
        average_error = sum(errors) / len(errors)
        if max_error > limits["max"]:
            failures.append(f"{job}: ranking single metric max error {max_error:.3f}% exceeds {limits['max']}%")
        if average_error > limits["average"]:
            failures.append(f"{job}: ranking single metric average error {average_error:.3f}% exceeds {limits['average']}%")

    if failures:
        raise AssertionError("\n".join(failures))

    print(f"OK: ranking single metric verified for {checked} samples")


def main() -> None:
    assert_ranking_single_metric()


if __name__ == "__main__":
    main()
