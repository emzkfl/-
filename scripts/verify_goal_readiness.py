from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.calc import API_OPTIONAL_SECTIONS, JOB_DETAIL_RULES, KMS_JOB_NAMES, build_view_model  # noqa: E402
from scripts.verify_calculation import (  # noqa: E402
    boss_board_failures,
    equipment_repair_annotation_failures,
    formula_integrity_failures,
    formula_manifest_failures,
    input_source_failures,
    recommendation_evidence_failures,
    readiness_failures,
    sample_raw,
    single_metric_failures,
)


REQUIRED_VIEW_KEYS = {
    "primaryMetric",
    "goalContract",
    "summary",
    "bossBoard",
    "bossBoardAudit",
    "itemUpgradePlan",
    "presetOptimization",
    "jobFormulaManifest",
    "formulaIntegrityAudit",
    "inputSourceAudit",
    "readinessAudit",
    "singleMetricAudit",
    "calculationCoverage",
}

REQUIRED_PLAN_KEYS = {
    "currentConverted",
    "basis",
    "upgradeTargets",
    "top",
    "all",
    "efficiencyProfile",
    "primaryEfficiency",
    "categorySummary",
    "primaryCategory",
    "slotSummary",
    "primarySlot",
    "weaknessSummary",
    "primaryWeakness",
    "repairChecklist",
    "repairRoadmap",
    "roadmapSummary",
    "repairTargetCount",
    "repairAudit",
    "repairEvidence",
    "repairFocus",
    "reliability",
}


def rule_sample_raw(rule: dict[str, Any]) -> dict[str, Any]:
    job = str(rule["keywords"][0])
    main_stat = str(rule["mainStat"])
    attack_type = str(rule["attackType"])
    stat_mode = str(rule.get("statMode") or "")
    if stat_mode == "demon_avenger":
        potential_line = "Max HP : +3%"
    elif stat_mode == "xenon":
        potential_line = "STR : +3%"
    else:
        potential_line = f"{main_stat} : +3%"
    raw = sample_raw(job, main_stat, attack_type, potential_line)
    raw["itemEquipment"]["preset_no"] = 1
    raw["itemEquipment"]["item_equipment_preset_1"] = raw["itemEquipment"]["item_equipment"]
    raw["ability"] = {"preset_no": 1, "ability_preset_1": {"ability_info": []}}
    raw["hyperStat"] = {"use_preset_no": "1", "hyper_stat_preset_1": []}
    return raw


def same_number(*values: Any) -> bool:
    converted = [int(round(float(value or 0))) for value in values]
    return len(set(converted)) == 1


def assert_unified_metric(view: dict[str, Any], context: str) -> list[str]:
    failures: list[str] = []
    primary = view.get("primaryMetric") or {}
    summary = view.get("summary") or {}
    plan = view.get("itemUpgradePlan") or {}
    preset = view.get("presetOptimization") or {}
    boss_board = view.get("bossBoard") or []
    used_by = primary.get("usedBy") or {}
    value = primary.get("value")

    if primary.get("id") != "unifiedConverted380":
        failures.append(f"{context}: primary metric id is not unifiedConverted380")
    if primary.get("source") != "hexaConverted380":
        failures.append(f"{context}: primary metric source is not hexaConverted380")
    if not same_number(
        value,
        summary.get("unifiedConverted380"),
        summary.get("bossBasisConverted380"),
        used_by.get("bossBoard"),
        used_by.get("itemUpgradePlan"),
        used_by.get("presetOptimization"),
        plan.get("currentConverted"),
        (preset.get("current") or {}).get("converted"),
        boss_board[0].get("currentConverted") if boss_board else 0,
    ):
        failures.append(f"{context}: unified metric values are not identical")
    failures.extend(single_metric_failures(view, context))
    return failures


def assert_repair_plan(view: dict[str, Any], context: str) -> list[str]:
    failures: list[str] = []
    plan = view.get("itemUpgradePlan") or {}
    missing = sorted(REQUIRED_PLAN_KEYS - set(plan))
    if missing:
        failures.append(f"{context}: itemUpgradePlan missing keys {missing}")
        return failures

    rows = plan.get("top") or []
    all_rows = plan.get("all") or []
    roadmap = plan.get("repairRoadmap") or []
    weakness_summary = plan.get("weaknessSummary") or []
    repair_focus = plan.get("repairFocus") or {}

    if not all_rows:
        failures.append(f"{context}: no item improvement candidates")
    if not rows:
        failures.append(f"{context}: no top item improvement candidates")
    if not roadmap:
        failures.append(f"{context}: no repair roadmap")
    if not weakness_summary:
        failures.append(f"{context}: no weakness summary")

    if rows:
        first = rows[0]
        required_row_fields = {
            "slot",
            "name",
            "currentState",
            "recommendedType",
            "recommendedAction",
            "reason",
            "metric",
            "metricBefore",
            "metricAfter",
            "expectedGain",
            "expectedGainPercent",
            "recommendationEvidence",
            "scenarios",
            "weaknesses",
        }
        missing_row_fields = sorted(required_row_fields - set(first))
        if missing_row_fields:
            failures.append(f"{context}: top candidate missing fields {missing_row_fields}")
        if first.get("expectedGain", 0) <= 0:
            failures.append(f"{context}: top expected gain is not positive")
        if first.get("metric") != "unifiedConverted380":
            failures.append(f"{context}: top metric is not unifiedConverted380")
        if first.get("metricBefore") != plan.get("currentConverted"):
            failures.append(f"{context}: top metric before does not match current converted")
        if first.get("metricAfter") != first.get("metricBefore", 0) + first.get("expectedGain", 0):
            failures.append(f"{context}: top metric after does not match expected gain")
        if first.get("expectedGainPercent", 0) <= 0:
            failures.append(f"{context}: top expected gain percent is not positive")
        if not first.get("slot") or not first.get("name"):
            failures.append(f"{context}: top candidate does not identify an item slot and name")
        if not first.get("recommendedType"):
            failures.append(f"{context}: top recommended type missing")
        if not first.get("recommendedAction"):
            failures.append(f"{context}: top recommended action missing")
        if not first.get("reason"):
            failures.append(f"{context}: top recommendation reason missing")
        if not first.get("weaknesses"):
            failures.append(f"{context}: top weaknesses missing")
        if not first.get("scenarios"):
            failures.append(f"{context}: top improvement scenarios missing")
        if not (first.get("recommendationEvidence") or {}).get("source"):
            failures.append(f"{context}: top recommendation evidence source missing")
        if plan.get("repairChecklist"):
            checklist_first = plan["repairChecklist"][0]
            for key in ("slot", "item", "type", "action", "description", "reason", "metric", "metricBefore", "metricAfter", "expectedGain", "weakness"):
                if not checklist_first.get(key):
                    failures.append(f"{context}: first checklist field {key} missing")
            if checklist_first.get("item") != first.get("name"):
                failures.append(f"{context}: first checklist item does not match top candidate")
            if checklist_first.get("expectedGain") != first.get("expectedGain"):
                failures.append(f"{context}: first checklist gain does not match top candidate")
            if checklist_first.get("slot") != first.get("slot"):
                failures.append(f"{context}: first checklist slot does not match top candidate")
            if checklist_first.get("action") != first.get("recommendedAction"):
                failures.append(f"{context}: first checklist action does not match top candidate")
            if checklist_first.get("metricBefore") != first.get("metricBefore"):
                failures.append(f"{context}: first checklist metric before does not match top candidate")
            if checklist_first.get("metricAfter") != first.get("metricAfter"):
                failures.append(f"{context}: first checklist metric after does not match top candidate")
        if repair_focus:
            if repair_focus.get("slot") != first.get("slot"):
                failures.append(f"{context}: repair focus slot does not match top candidate")
            if repair_focus.get("category") != first.get("recommendedType"):
                failures.append(f"{context}: repair focus category does not match top candidate")
            if repair_focus.get("expectedGain") != first.get("expectedGain"):
                failures.append(f"{context}: repair focus gain does not match top candidate")
            if not repair_focus.get("description"):
                failures.append(f"{context}: repair focus description missing")
        else:
            failures.append(f"{context}: repair focus missing")

    if roadmap:
        current = int(round(float(plan.get("currentConverted") or 0)))
        first_projected = int(round(float(roadmap[0].get("projectedConverted") or 0)))
        if first_projected <= current:
            failures.append(f"{context}: first roadmap step does not increase unified converted score")
        if (plan.get("roadmapSummary") or {}).get("projectedConverted") != roadmap[-1].get("projectedConverted"):
            failures.append(f"{context}: roadmap summary does not match final roadmap step")

    if weakness_summary and plan.get("primaryWeakness") != weakness_summary[0]:
        failures.append(f"{context}: primary weakness does not match first weakness summary row")
    if (plan.get("repairAudit") or {}).get("allPassed") is not True:
        failures.append(f"{context}: repair audit did not pass")

    failures.extend(recommendation_evidence_failures(plan, context))
    return failures


def assert_upgrade_targets(rule: dict[str, Any], view: dict[str, Any], context: str) -> list[str]:
    plan = view.get("itemUpgradePlan") or {}
    targets = plan.get("upgradeTargets") or []
    main_stat = str(rule.get("mainStat") or "")
    stat_mode = str(rule.get("statMode") or "")
    if stat_mode == "demon_avenger":
        expected = ["최대 HP"]
    elif stat_mode == "xenon":
        expected = ["STR", "DEX", "LUK"]
    else:
        expected = [main_stat]
    if targets != expected:
        return [f"{context}: upgrade targets {targets} != {expected}"]
    return []


def assert_goal_contract(view: dict[str, Any], context: str) -> list[str]:
    contract = view.get("goalContract") or {}
    primary = view.get("primaryMetric") or {}
    summary = view.get("summary") or {}
    plan = view.get("itemUpgradePlan") or {}
    boss_audit = view.get("bossBoardAudit") or {}
    formula_manifest = view.get("jobFormulaManifest") or {}
    current_formula = formula_manifest.get("current") or {}
    failures: list[str] = []

    required_keys = {
        "version",
        "status",
        "metricId",
        "metricValue",
        "basis",
        "source",
        "canCompareUsers",
        "canJudgeBosses",
        "canRecommendItems",
        "usedBy",
        "repairFocus",
        "repairChecklistCount",
        "jobFormulaCount",
        "currentJob",
        "fieldPaths",
        "checks",
        "failedCheckIds",
    }
    missing = sorted(required_keys - set(contract))
    if missing:
        failures.append(f"{context}: goal contract missing keys {missing}")
        return failures

    if contract.get("version") != "single_metric_repair_v1":
        failures.append(f"{context}: goal contract version mismatch")
    if contract.get("metricId") != "unifiedConverted380":
        failures.append(f"{context}: goal contract metric id mismatch")
    if contract.get("metricValue") != primary.get("value"):
        failures.append(f"{context}: goal contract metric value mismatch")
    if contract.get("metricValue") != summary.get("unifiedConverted380"):
        failures.append(f"{context}: goal contract summary value mismatch")
    if contract.get("basis") != summary.get("unifiedBasis"):
        failures.append(f"{context}: goal contract basis mismatch")
    if contract.get("source") != primary.get("source"):
        failures.append(f"{context}: goal contract source mismatch")
    if contract.get("jobFormulaCount") != len(KMS_JOB_NAMES):
        failures.append(f"{context}: goal contract job formula count mismatch")
    if contract.get("currentJob") != current_formula.get("job"):
        failures.append(f"{context}: goal contract current job mismatch")
    if contract.get("repairFocus") != plan.get("repairFocus"):
        failures.append(f"{context}: goal contract repair focus mismatch")
    if contract.get("repairChecklistCount") != len(plan.get("repairChecklist") or []):
        failures.append(f"{context}: goal contract checklist count mismatch")

    used_by = contract.get("usedBy") or {}
    if used_by.get("bossBoard") != primary.get("usedBy", {}).get("bossBoard"):
        failures.append(f"{context}: goal contract boss metric mismatch")
    if used_by.get("itemUpgradePlan") != plan.get("currentConverted"):
        failures.append(f"{context}: goal contract repair metric mismatch")
    if not contract.get("canCompareUsers"):
        failures.append(f"{context}: goal contract does not allow user comparison")
    if not contract.get("canJudgeBosses"):
        failures.append(f"{context}: goal contract does not allow boss judgment")
    if not contract.get("canRecommendItems"):
        failures.append(f"{context}: goal contract does not allow item recommendation")
    if contract.get("status") not in {"ready", "caution"}:
        failures.append(f"{context}: goal contract status is {contract.get('status')!r}")

    checks = contract.get("checks") or []
    check_ids = {row.get("id") for row in checks}
    expected_check_ids = {"metricConfidence", "singleMetric", "kmsJobFormula", "apiInput", "bossBoard", "itemRepair"}
    if check_ids != expected_check_ids:
        failures.append(f"{context}: goal contract checks mismatch {check_ids}")
    boss_check = next((row for row in checks if row.get("id") == "bossBoard"), {})
    if boss_check.get("passed") is not True:
        failures.append(f"{context}: goal contract boss check failed {boss_check}")
    if boss_check.get("detail") != f"{boss_audit.get('ruleCount')}개 · {boss_audit.get('ratioFormula') or '-'}":
        failures.append(f"{context}: goal contract boss check detail mismatch")
    failed_ids = [row.get("id") for row in checks if not row.get("passed")]
    if failed_ids != contract.get("failedCheckIds"):
        failures.append(f"{context}: goal contract failed ids mismatch")
    if contract.get("failedCheckIds"):
        failures.append(f"{context}: goal contract has failed checks {contract.get('failedCheckIds')}")

    field_paths = contract.get("fieldPaths") or {}
    expected_paths = {
        "representativeMetric": "primaryMetric.value",
        "bossMetric": "bossBoard[0].currentConverted",
        "bossAudit": "bossBoardAudit",
        "presetMetric": "presetOptimization.current.converted",
        "repairMetric": "itemUpgradePlan.currentConverted",
        "repairFocus": "itemUpgradePlan.repairFocus",
        "repairChecklist": "itemUpgradePlan.repairChecklist",
    }
    if field_paths != expected_paths:
        failures.append(f"{context}: goal contract field paths mismatch")

    return failures


def assert_job_view(rule: dict[str, Any]) -> list[str]:
    job = str(rule["keywords"][0])
    view = build_view_model(rule_sample_raw(rule))
    context = f"job {job}"
    failures: list[str] = []

    missing_view_keys = sorted(REQUIRED_VIEW_KEYS - set(view))
    if missing_view_keys:
        failures.append(f"{context}: view missing keys {missing_view_keys}")
        return failures

    summary = view.get("summary") or {}
    primary = view.get("primaryMetric") or {}
    manifest = view.get("jobFormulaManifest") or {}
    coverage = view.get("calculationCoverage") or {}
    current = coverage.get("current") or {}

    if summary.get("formulaStatus") != "complete":
        failures.append(f"{context}: formula status is not complete")
    if current.get("job") != job:
        failures.append(f"{context}: coverage current job mismatch {current.get('job')!r}")
    if current.get("detailRuleApplied") is not True:
        failures.append(f"{context}: detail rule was not applied")
    if current.get("calibrationConfidence") != "high":
        failures.append(f"{context}: calibration confidence is not high")
    if (manifest.get("current") or {}).get("job") != job:
        failures.append(f"{context}: manifest current job mismatch")
    if primary.get("confidence", {}).get("score", 0) < 70:
        failures.append(f"{context}: primary metric confidence below 70")

    failures.extend(assert_unified_metric(view, context))
    failures.extend(boss_board_failures(view, context))
    failures.extend(assert_repair_plan(view, context))
    failures.extend(equipment_repair_annotation_failures(view, context))
    failures.extend(assert_upgrade_targets(rule, view, context))
    failures.extend(assert_goal_contract(view, context))
    failures.extend(formula_manifest_failures(manifest, context, job))
    failures.extend(formula_integrity_failures(view, context))
    failures.extend(input_source_failures(view, context))
    failures.extend(readiness_failures(view, context, {"ready", "caution"}))
    return failures


def assert_optional_api_failure_resilience(rule: dict[str, Any]) -> list[str]:
    job = str(rule["keywords"][0])
    context = f"optional API failure {job}"
    raw = rule_sample_raw(rule)
    failed_sections = {
        "hexamatrix",
        "hexamatrixStat",
        "linkSkill",
        "vmatrix",
        "skill5",
        "skill6",
    }
    raw["warnings"] = [
        {"section": section, "message": "sample optional API failure"}
        for section in sorted(failed_sections)
    ]
    for section in failed_sections:
        raw.pop(section, None)

    view = build_view_model(raw)
    quality = view.get("apiDataQuality") or {}
    failures: list[str] = []

    if quality.get("status") != "warning":
        failures.append(f"{context}: API quality status is not warning")
    if quality.get("missingRequiredSections"):
        failures.append(f"{context}: required sections are missing {quality.get('missingRequiredSections')}")
    if not failed_sections.issubset(set(quality.get("warningSections") or [])):
        failures.append(f"{context}: warning sections do not include failed optional sections")
    if not failed_sections.issubset(set(quality.get("missingOptionalSections") or [])):
        failures.append(f"{context}: missing optional sections do not include failed optional sections")
    for section in failed_sections:
        if section not in API_OPTIONAL_SECTIONS:
            failures.append(f"{context}: failed section {section} is not registered optional API")

    failures.extend(assert_unified_metric(view, context))
    failures.extend(assert_repair_plan(view, context))
    failures.extend(input_source_failures(view, context))
    failures.extend(readiness_failures(view, context, {"ready", "caution"}))
    return failures


def assert_goal_readiness() -> None:
    failures: list[str] = []
    if len(KMS_JOB_NAMES) != len(JOB_DETAIL_RULES):
        failures.append("KMS job names and detail rules have different lengths")
    if len(KMS_JOB_NAMES) < 48:
        failures.append(f"expected at least 48 KMS jobs, got {len(KMS_JOB_NAMES)}")
    if "레테" not in KMS_JOB_NAMES:
        failures.append("Lete job rule is missing")

    for rule in JOB_DETAIL_RULES:
        failures.extend(assert_job_view(rule))
        failures.extend(assert_optional_api_failure_resilience(rule))

    if failures:
        raise AssertionError("\n".join(failures))


def main() -> None:
    assert_goal_readiness()
    print(f"OK: goal readiness verified for {len(KMS_JOB_NAMES)} KMS jobs")


if __name__ == "__main__":
    main()
