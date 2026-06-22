from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app"))

from app.calc import (  # noqa: E402
    API_OPTIONAL_SECTIONS,
    API_REQUIRED_SECTIONS,
    BOSS_RULES,
    JOB_DETAIL_RULES,
    KMS_JOB_NAMES,
    build_view_model,
    calculation_coverage,
    job_formula_manifest,
)
from scripts.verify_calculation import boss_board_failures, formula_integrity_failures  # noqa: E402
from scripts.verify_goal_readiness import (  # noqa: E402
    assert_goal_readiness,
    rule_sample_raw,
    single_metric_failures,
    unified_repair_audit_failures,
)
from scripts.verify_nexon_endpoint_contract import assert_nexon_endpoint_contract  # noqa: E402
from scripts.verify_ranking_single_metric import assert_ranking_single_metric  # noqa: E402


MIN_RANKING_SAMPLES = 1440
REQUIRED_GOAL_FIELD_PATHS = {
    "representativeMetric": "primaryMetric.value",
    "bossMetric": "bossBoard[0].currentConverted",
    "bossEffectiveMetric": "bossBoard[0].effectiveConverted",
    "bossAudit": "bossBoardAudit",
    "presetMetric": "presetOptimization.current.converted",
    "repairMetric": "itemUpgradePlan.currentConverted",
    "repairFocus": "itemUpgradePlan.repairFocus",
    "repairChecklist": "itemUpgradePlan.repairChecklist",
    "repairDecisionMatrix": "itemUpgradePlan.repairDecisionMatrix",
}


def assert_formula_catalog() -> None:
    failures: list[str] = []
    manifest = job_formula_manifest("레테")
    coverage = calculation_coverage("레테")
    jobs = manifest.get("jobs") or []
    known_jobs = manifest.get("knownJobs") or []

    if len(KMS_JOB_NAMES) != 48:
        failures.append(f"KMS job count must be exactly 48, got {len(KMS_JOB_NAMES)}")
    if len(JOB_DETAIL_RULES) != len(KMS_JOB_NAMES):
        failures.append("KMS job rules and names have different lengths")
    if "레테" not in KMS_JOB_NAMES:
        failures.append("레테 is missing from KMS job formulas")
    if manifest.get("jobCount") != len(KMS_JOB_NAMES):
        failures.append("formula manifest job count mismatch")
    if set(known_jobs) != set(KMS_JOB_NAMES):
        failures.append("formula manifest known job set mismatch")
    if len(jobs) != len(KMS_JOB_NAMES):
        failures.append("formula manifest job row count mismatch")
    if coverage.get("missingDetailJobs") or coverage.get("missingMultiplierJobs") or coverage.get("missingCombatJobs"):
        failures.append(f"formula coverage has missing jobs: {coverage}")

    lete = next((row for row in jobs if row.get("job") == "레테"), None)
    if not lete:
        failures.append("formula manifest does not expose 레테")
    elif lete.get("mainStat") != "INT" or lete.get("attackType") != "마력":
        failures.append(f"레테 formula row has unexpected basis: {lete}")

    for row in jobs:
        job = str(row.get("job") or "")
        if not row.get("mainStat") or not row.get("attackType"):
            failures.append(f"{job}: missing main stat or attack type")
        if float(row.get("weaponConstant") or 0) <= 0:
            failures.append(f"{job}: missing weapon constant")
        if float(row.get("mastery") or 0) <= 0:
            failures.append(f"{job}: missing mastery")
        if float(row.get("jobConvertedMultiplier") or 0) <= 0:
            failures.append(f"{job}: missing converted multiplier")

    if failures:
        raise AssertionError("\n".join(failures))


def assert_boss_rules_are_adjusted() -> None:
    failures: list[str] = []
    if len(BOSS_RULES) < 20:
        failures.append(f"boss rule count too small: {len(BOSS_RULES)}")

    force_types = {str(row.get("forceType") or "") for row in BOSS_RULES}
    if "arcane" not in force_types or "authentic" not in force_types:
        failures.append(f"boss rules do not include arcane/authentic force types: {force_types}")
    if not any(int(row.get("defense") or 0) == 380 for row in BOSS_RULES):
        failures.append("boss rules do not include 380 defense bosses")
    if not any(int(row.get("defense") or 0) == 300 for row in BOSS_RULES):
        failures.append("boss rules do not include 300 defense bosses")

    for row in BOSS_RULES:
        name = str(row.get("name") or "")
        if int(row.get("defense") or 0) <= 0:
            failures.append(f"{name}: defense missing")
        if str(row.get("forceType") or "") in {"arcane", "authentic"} and int(row.get("forceRequired") or 0) <= 0:
            failures.append(f"{name}: force requirement missing")
        if float(row.get("party") or 0) <= 0 or float(row.get("solo") or 0) <= 0:
            failures.append(f"{name}: party/solo requirement missing")
        if int(row.get("totalHp") or 0) <= 0:
            failures.append(f"{name}: total HP missing")
        if float(row.get("timeLimitMinutes") or 0) <= 0:
            failures.append(f"{name}: time limit missing")
        if float(row.get("hpRatio") or 0) <= 0:
            failures.append(f"{name}: HP ratio missing")
        if not str(row.get("sourceUrl") or "").startswith("https://namu.wiki/w/"):
            failures.append(f"{name}: NamuWiki source URL missing")

    if failures:
        raise AssertionError("\n".join(failures))


def assert_view_goal_contract(view: dict[str, Any], job: str) -> list[str]:
    failures: list[str] = []
    primary = view.get("primaryMetric") or {}
    contract = view.get("goalContract") or {}
    plan = view.get("itemUpgradePlan") or {}
    boss_board = view.get("bossBoard") or []
    boss_audit = view.get("bossBoardAudit") or {}

    if primary.get("id") != "unifiedConverted380":
        failures.append(f"{job}: representative metric id drifted")
    if contract.get("metricValue") != primary.get("value"):
        failures.append(f"{job}: goal contract does not use representative metric")
    if contract.get("canCompareUsers") is not True:
        failures.append(f"{job}: goal contract cannot compare users")
    if contract.get("canJudgeBosses") is not True:
        failures.append(f"{job}: goal contract cannot judge bosses")
    if contract.get("canRecommendItems") is not True:
        failures.append(f"{job}: goal contract cannot recommend item repairs")
    if contract.get("fieldPaths") != REQUIRED_GOAL_FIELD_PATHS:
        failures.append(f"{job}: goal field paths do not include current boss effective metric")
    if plan.get("currentConverted") != primary.get("value"):
        failures.append(f"{job}: item repair plan is not based on representative metric")
    if not plan.get("repairChecklist") or not plan.get("repairDecisionMatrix"):
        failures.append(f"{job}: item repair checklist or decision matrix missing")
    if (plan.get("repairAudit") or {}).get("allPassed") is not True:
        failures.append(f"{job}: item repair audit failed")

    if boss_audit.get("ratioFormula") != "effectiveConverted / requiredConverted * 100":
        failures.append(f"{job}: boss ratio does not use effective converted metric")
    if "방어율보정" not in str(boss_audit.get("effectiveMetricFormula") or ""):
        failures.append(f"{job}: boss audit does not expose defense/force adjustment formula")
    for boss in boss_board:
        adjustment = boss.get("bossAdjustment") or {}
        force = adjustment.get("force") or {}
        armor = adjustment.get("armor") or {}
        if not boss.get("effectiveConverted"):
            failures.append(f"{job}/{boss.get('name')}: effective boss metric missing")
        if "damageMultiplier" not in adjustment:
            failures.append(f"{job}/{boss.get('name')}: boss damage multiplier missing")
        if armor.get("bossDefense") is None:
            failures.append(f"{job}/{boss.get('name')}: boss defense adjustment missing")
        if force.get("damageMultiplier") is None:
            failures.append(f"{job}/{boss.get('name')}: boss force adjustment missing")

    failures.extend(single_metric_failures(view, job))
    failures.extend(boss_board_failures(view, job))
    failures.extend(formula_integrity_failures(view, job))
    failures.extend(unified_repair_audit_failures(view, job))
    return failures


def assert_all_job_views() -> None:
    failures: list[str] = []
    for rule in JOB_DETAIL_RULES:
        job = str(rule["keywords"][0])
        view = build_view_model(rule_sample_raw(rule))
        failures.extend(assert_view_goal_contract(view, job))

    if failures:
        raise AssertionError("\n".join(failures))


def assert_ranking_artifact_scope() -> None:
    path = ROOT / "calibration-rankings.json"
    if not path.exists():
        raise AssertionError("calibration-rankings.json is missing")

    data = json.loads(path.read_text(encoding="utf-8"))
    samples = data.get("samples") or {}
    count = sum(len(rows or []) for rows in samples.values())
    if set(samples) != set(KMS_JOB_NAMES):
        missing = sorted(set(KMS_JOB_NAMES) - set(samples))
        extra = sorted(set(samples) - set(KMS_JOB_NAMES))
        raise AssertionError(f"ranking sample job set mismatch missing={missing} extra={extra}")
    if count < MIN_RANKING_SAMPLES:
        raise AssertionError(f"ranking sample count {count} < {MIN_RANKING_SAMPLES}")


def assert_api_contract_scope() -> None:
    expected_sections = set(API_REQUIRED_SECTIONS) | set(API_OPTIONAL_SECTIONS)
    required_for_goal = {
        "basic",
        "stat",
        "itemEquipment",
        "symbol",
        "ability",
        "hyperStat",
        "hexamatrix",
        "hexamatrixStat",
        "linkSkill",
        "vmatrix",
        "skill5",
        "skill6",
        "petEquipment",
        "ringExchangeSkillEquipment",
        "ringReserveSkillEquipment",
    }
    missing = sorted(required_for_goal - expected_sections)
    if missing:
        raise AssertionError(f"goal-required API sections missing from contract: {missing}")


def main() -> None:
    assert_formula_catalog()
    assert_boss_rules_are_adjusted()
    assert_api_contract_scope()
    assert_nexon_endpoint_contract()
    assert_goal_readiness()
    assert_all_job_views()
    assert_ranking_artifact_scope()
    assert_ranking_single_metric()
    print(
        "OK: goal completion contract verified "
        f"({len(KMS_JOB_NAMES)} jobs, {len(BOSS_RULES)} bosses, >= {MIN_RANKING_SAMPLES} ranking samples)"
    )


if __name__ == "__main__":
    main()
