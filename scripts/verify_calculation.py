from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.calc import (  # noqa: E402
    CALIBRATION_EVIDENCE,
    COMBAT_CONVERTED_JOB_FACTORS,
    JOB_CONVERTED_MULTIPLIERS,
    JOB_DETAIL_RULES,
    K_ATTACK,
    K_BOSS,
    K_CRIT_DAMAGE,
    K_CRIT_RATE,
    K_DAMAGE,
    K_FINAL,
    K_IED,
    K_MAGIC,
    KMS_JOB_NAMES,
    SPECIAL_COMBAT_CONVERTED_MODELS,
    build_view_model,
    calculation_coverage,
    job_formula_manifest,
    job_detail_rule,
    primary_job_name,
    profile_from_lines,
)


def table_jobs(rows: list[dict] | tuple[dict, ...]) -> set[str]:
    return {str(row["keywords"][0]) for row in rows}


def single_metric_failures(view: dict, context: str) -> list[str]:
    failures: list[str] = []
    primary = view.get("primaryMetric") or {}
    summary = view.get("summary") or {}
    audit = view.get("singleMetricAudit") or {}
    expected_targets = {
        "summary.unifiedConverted380",
        "summary.bossBasisConverted380",
        "primaryMetric.usedBy.bossBoard",
        "primaryMetric.usedBy.itemUpgradePlan",
        "primaryMetric.usedBy.presetOptimization",
        "itemUpgradePlan.currentConverted",
        "presetOptimization.current.converted",
        "bossBoard[0].currentConverted",
    }

    if not audit:
        return [f"{context}: single metric audit missing"]
    if audit.get("metricId") != primary.get("id"):
        failures.append(f"{context}: single metric audit id mismatch")
    if audit.get("basis") != summary.get("unifiedBasis"):
        failures.append(f"{context}: single metric audit basis mismatch")
    if audit.get("value") != primary.get("value"):
        failures.append(f"{context}: single metric audit value mismatch")
    if audit.get("value") != summary.get("unifiedConverted380"):
        failures.append(f"{context}: single metric audit does not match summary")
    if not audit.get("allMatched"):
        failures.append(f"{context}: single metric audit has mismatches {audit.get('checks')}")
    checks = audit.get("checks") or []
    targets = {row.get("target") for row in checks}
    missing_targets = sorted(expected_targets - targets)
    if missing_targets:
        failures.append(f"{context}: single metric audit missing targets {missing_targets}")
    for row in checks:
        if row.get("value") != audit.get("value") or not row.get("matches"):
            failures.append(f"{context}: single metric check failed {row}")
    return failures


def formula_manifest_failures(manifest: dict, context: str, expected_job: str | None = None) -> list[str]:
    failures: list[str] = []
    jobs = manifest.get("jobs") or []
    known_jobs = manifest.get("knownJobs") or []
    job_set = set(KMS_JOB_NAMES)
    manifest_jobs = {str(row.get("job") or "") for row in jobs}

    if manifest.get("jobCount") != len(KMS_JOB_NAMES):
        failures.append(f"{context}: manifest job count mismatch")
    if set(known_jobs) != job_set:
        failures.append(f"{context}: manifest known jobs mismatch")
    if manifest_jobs != job_set:
        failures.append(f"{context}: manifest row jobs mismatch")

    for row in jobs:
        job = str(row.get("job") or "")
        if not row.get("aliases") or row["aliases"][0] != job:
            failures.append(f"{context}/{job}: aliases missing primary job")
        if not row.get("mainStat"):
            failures.append(f"{context}/{job}: main stat missing")
        if not row.get("attackType"):
            failures.append(f"{context}/{job}: attack type missing")
        if float(row.get("weaponConstant") or 0) <= 0:
            failures.append(f"{context}/{job}: weapon constant invalid")
        if float(row.get("calibratedWeaponConstant") or 0) <= 0:
            failures.append(f"{context}/{job}: calibrated weapon constant invalid")
        if float(row.get("mastery") or 0) <= 0:
            failures.append(f"{context}/{job}: mastery invalid")
        if float(row.get("jobConvertedMultiplier") or 0) <= 0:
            failures.append(f"{context}/{job}: converted multiplier invalid")
        if float(row.get("combatPowerJobFactor") or 0) <= 0:
            failures.append(f"{context}/{job}: combat power factor invalid")
        if not row.get("upgradeTargets"):
            failures.append(f"{context}/{job}: upgrade targets missing")

    current = manifest.get("current") or {}
    if expected_job:
        if current.get("job") != expected_job:
            failures.append(f"{context}: current manifest job {current.get('job')} != {expected_job}")
        if not current.get("matched"):
            failures.append(f"{context}: current manifest did not match a detailed rule")
    return failures


def recommendation_evidence_failures(plan: dict, context: str) -> list[str]:
    failures: list[str] = []
    rows = plan.get("top") or []
    summary = plan.get("repairEvidence") or {}
    audit = plan.get("repairAudit") or {}
    weakness_summary = plan.get("weaknessSummary") or []
    roadmap = plan.get("repairRoadmap") or []
    roadmap_summary = plan.get("roadmapSummary") or {}

    if not summary:
        failures.append(f"{context}: repair evidence summary missing")
    elif summary.get("basis") != plan.get("basis"):
        failures.append(f"{context}: repair evidence basis mismatch")
    elif summary.get("metric") != "unifiedConverted380":
        failures.append(f"{context}: repair evidence metric mismatch")
    elif summary.get("candidateCount") != len(plan.get("all") or rows):
        failures.append(f"{context}: repair evidence candidate count mismatch")

    for row in rows:
        evidence = row.get("recommendationEvidence") or {}
        if not evidence:
            failures.append(f"{context}/{row.get('name')}: recommendation evidence missing")
            continue
        if evidence.get("basis") != plan.get("basis"):
            failures.append(f"{context}/{row.get('name')}: evidence basis mismatch")
        if evidence.get("metric") != "unifiedConverted380":
            failures.append(f"{context}/{row.get('name')}: evidence metric mismatch")
        if evidence.get("priorityFormula") != "expectedGain + contribution * 0.05":
            failures.append(f"{context}/{row.get('name')}: priority formula mismatch")
        if evidence.get("expectedGain") != row.get("expectedGain"):
            failures.append(f"{context}/{row.get('name')}: evidence expected gain mismatch")
        if evidence.get("contribution") != row.get("contribution"):
            failures.append(f"{context}/{row.get('name')}: evidence contribution mismatch")
        if evidence.get("priorityScore") != row.get("priorityScore"):
            failures.append(f"{context}/{row.get('name')}: evidence priority score mismatch")
        if row.get("weaknesses"):
            weakness = row["weaknesses"][0]
            if evidence.get("weaknessLabel") != weakness.get("label"):
                failures.append(f"{context}/{row.get('name')}: evidence weakness label mismatch")
            if evidence.get("weaknessGap") != weakness.get("gap"):
                failures.append(f"{context}/{row.get('name')}: evidence weakness gap mismatch")

    if rows and summary.get("top", {}).get("item") != rows[0].get("name"):
        failures.append(f"{context}: repair evidence top item mismatch")
    for checklist_row in plan.get("repairChecklist") or []:
        if not checklist_row.get("recommendationEvidence"):
            failures.append(f"{context}: checklist recommendation evidence missing")
    weakness_labels = {weakness.get("label") for row in rows for weakness in (row.get("weaknesses") or [])}
    summary_labels = {row.get("label") for row in weakness_summary}
    if rows and not weakness_summary:
        failures.append(f"{context}: weakness summary missing")
    if not summary_labels.issubset(weakness_labels):
        failures.append(f"{context}: weakness summary has unknown labels {sorted(summary_labels - weakness_labels)}")
    for row in weakness_summary:
        if row.get("candidateCount", 0) <= 0:
            failures.append(f"{context}/{row.get('label')}: weakness candidate count missing")
        if row.get("priorityScore", 0) <= 0:
            failures.append(f"{context}/{row.get('label')}: weakness priority score missing")
        if not row.get("bestItem"):
            failures.append(f"{context}/{row.get('label')}: weakness best item missing")
    if rows and not roadmap:
        failures.append(f"{context}: repair roadmap missing")
    if roadmap:
        if roadmap_summary.get("stepCount") != len(roadmap):
            failures.append(f"{context}: roadmap summary step count mismatch")
        if roadmap_summary.get("basis") != plan.get("basis"):
            failures.append(f"{context}: roadmap summary basis mismatch")
        previous_projected = plan.get("currentConverted") or 0
        previous_cumulative = 0
        for index, step in enumerate(roadmap, 1):
            source = rows[index - 1] if index - 1 < len(rows) else {}
            if step.get("rank") != index:
                failures.append(f"{context}: roadmap rank mismatch {step}")
            if step.get("item") != source.get("name"):
                failures.append(f"{context}: roadmap item mismatch {step}")
            if step.get("expectedGain") != source.get("expectedGain"):
                failures.append(f"{context}: roadmap expected gain mismatch {step}")
            if step.get("cumulativeGain", 0) < previous_cumulative:
                failures.append(f"{context}: roadmap cumulative gain decreased {step}")
            if step.get("projectedConverted", 0) < previous_projected:
                failures.append(f"{context}: roadmap projected converted decreased {step}")
            previous_cumulative = step.get("cumulativeGain", previous_cumulative)
            previous_projected = step.get("projectedConverted", previous_projected)
        if roadmap_summary.get("projectedConverted") != roadmap[-1].get("projectedConverted"):
            failures.append(f"{context}: roadmap summary projected converted mismatch")
    if not audit:
        failures.append(f"{context}: repair audit missing")
    else:
        if audit.get("basis") != plan.get("basis"):
            failures.append(f"{context}: repair audit basis mismatch")
        if audit.get("metric") != "unifiedConverted380":
            failures.append(f"{context}: repair audit metric mismatch")
        if not audit.get("allPassed"):
            failures.append(f"{context}: repair audit failed {audit.get('checks')}")
        if audit.get("candidateCount") != len(plan.get("all") or rows):
            failures.append(f"{context}: repair audit candidate count mismatch")
        if rows:
            if audit.get("topItem") != rows[0].get("name"):
                failures.append(f"{context}: repair audit top item mismatch")
            if audit.get("topAction") != rows[0].get("recommendedAction"):
                failures.append(f"{context}: repair audit top action mismatch")
            if audit.get("topExpectedGain") != rows[0].get("expectedGain"):
                failures.append(f"{context}: repair audit top gain mismatch")
    return failures


def formula_integrity_failures(view: dict, context: str) -> list[str]:
    failures: list[str] = []
    audit = view.get("formulaIntegrityAudit") or {}
    expected_labels = {
        "주스탯 공식",
        "공격력 공식",
        "주스탯 계수",
        "보공+데미지 합성",
        "일반 데미지 계수",
        "숙련도 평균",
        "damage_factor",
        "raw 환산",
        "상세 환산",
        "HEXA 환산",
        "대표 환산",
    }
    checks = audit.get("checks") or []
    labels = {row.get("label") for row in checks}
    if not audit:
        return [f"{context}: formula integrity audit missing"]
    if audit.get("metric") != "unifiedConverted380":
        failures.append(f"{context}: formula integrity metric mismatch")
    if audit.get("checkCount") != len(checks):
        failures.append(f"{context}: formula integrity check count mismatch")
    if labels != expected_labels:
        failures.append(f"{context}: formula integrity labels mismatch missing={sorted(expected_labels - labels)} extra={sorted(labels - expected_labels)}")
    if not audit.get("allPassed"):
        failures.append(f"{context}: formula integrity failed {checks}")
    if audit.get("failedCount") != 0:
        failures.append(f"{context}: formula integrity failed count {audit.get('failedCount')}")
    for row in checks:
        if not row.get("passed"):
            failures.append(f"{context}: formula check failed {row}")
        if "actual" not in row or "expected" not in row or "delta" not in row:
            failures.append(f"{context}: formula check lacks values {row}")
    return failures


def input_source_failures(view: dict, context: str) -> list[str]:
    failures: list[str] = []
    audit = view.get("inputSourceAudit") or {}
    expected_targets = {
        "primaryMetric",
        "bossBoard",
        "itemUpgradePlan",
        "presetOptimization",
        "hexaConvertedDetail",
        "extra",
    }
    if not audit:
        return [f"{context}: input source audit missing"]
    rows = audit.get("rows") or []
    targets = {row.get("target") for row in rows}
    if targets != expected_targets:
        failures.append(f"{context}: input source targets mismatch missing={sorted(expected_targets - targets)} extra={sorted(targets - expected_targets)}")
    if not audit.get("allRequiredPresent"):
        failures.append(f"{context}: required input sources missing {rows}")
    if audit.get("usageCount") != len(expected_targets):
        failures.append(f"{context}: input source usage count mismatch")
    for row in rows:
        if row.get("presentRequired") != row.get("requiredTotal"):
            failures.append(f"{context}/{row.get('target')}: required source missing")
        if row.get("status") not in {"complete", "partial", "warning", "blocked"}:
            failures.append(f"{context}/{row.get('target')}: invalid source status {row.get('status')}")
        if not row.get("reason"):
            failures.append(f"{context}/{row.get('target')}: source reason missing")
    return failures


def readiness_failures(view: dict, context: str, expected_statuses: set[str] | None = None) -> list[str]:
    failures: list[str] = []
    audit = view.get("readinessAudit") or {}
    expected_labels = {
        "대표 지표 신뢰도",
        "단일 지표 연결",
        "계산식 재검산",
        "입력 API",
        "직업 공식",
        "장비 개선 추천",
        "개선 로드맵",
    }
    if not audit:
        return [f"{context}: readiness audit missing"]
    checks = audit.get("checks") or []
    labels = {row.get("label") for row in checks}
    if labels != expected_labels:
        failures.append(f"{context}: readiness checks mismatch missing={sorted(expected_labels - labels)} extra={sorted(labels - expected_labels)}")
    if audit.get("checkCount") != len(checks):
        failures.append(f"{context}: readiness check count mismatch")
    if audit.get("passedCount", 0) + audit.get("failedCount", 0) != audit.get("checkCount"):
        failures.append(f"{context}: readiness pass/fail count mismatch")
    if audit.get("metric") != "unifiedConverted380":
        failures.append(f"{context}: readiness metric mismatch")
    if expected_statuses and audit.get("status") not in expected_statuses:
        failures.append(f"{context}: readiness status {audit.get('status')} not in {expected_statuses}")
    for row in checks:
        if "passed" not in row or not row.get("detail"):
            failures.append(f"{context}: readiness check incomplete {row}")
    return failures


def assert_job_table_integrity() -> None:
    failures: list[str] = []
    job_set = set(KMS_JOB_NAMES)
    aliases: dict[str, str] = {}
    if len(KMS_JOB_NAMES) != len(job_set):
        failures.append("KMS_JOB_NAMES has duplicate entries")
    if len(JOB_DETAIL_RULES) != len(KMS_JOB_NAMES):
        failures.append(f"detail rule count drift {len(JOB_DETAIL_RULES)} != {len(KMS_JOB_NAMES)}")
    if table_jobs(JOB_DETAIL_RULES) != job_set:
        failures.append("detail rule job set differs from KMS_JOB_NAMES")
    if table_jobs(JOB_CONVERTED_MULTIPLIERS) != job_set:
        missing = sorted(job_set - table_jobs(JOB_CONVERTED_MULTIPLIERS))
        extra = sorted(table_jobs(JOB_CONVERTED_MULTIPLIERS) - job_set)
        failures.append(f"converted multiplier job set mismatch missing={missing} extra={extra}")
    if set(CALIBRATION_EVIDENCE) != job_set:
        missing = sorted(job_set - set(CALIBRATION_EVIDENCE))
        extra = sorted(set(CALIBRATION_EVIDENCE) - job_set)
        failures.append(f"calibration evidence job set mismatch missing={missing} extra={extra}")

    combat_jobs = table_jobs(COMBAT_CONVERTED_JOB_FACTORS) | table_jobs(SPECIAL_COMBAT_CONVERTED_MODELS)
    if combat_jobs != job_set:
        missing = sorted(job_set - combat_jobs)
        extra = sorted(combat_jobs - job_set)
        failures.append(f"combat model job set mismatch missing={missing} extra={extra}")

    failures.extend(formula_manifest_failures(job_formula_manifest("레테"), "global manifest", "레테"))

    for rule in JOB_DETAIL_RULES:
        job = str(rule["keywords"][0])
        for keyword in rule["keywords"]:
            keyword = str(keyword)
            if keyword in aliases:
                failures.append(f"{job}: duplicate alias {keyword!r} already used by {aliases[keyword]}")
            aliases[keyword] = job

            matched = job_detail_rule(keyword)
            matched_job = primary_job_name(matched)
            if matched_job != job:
                failures.append(f"{job}: alias {keyword!r} resolves to {matched_job!r}")

            decorated = f"Lv.285 {keyword} 검증"
            decorated_match = primary_job_name(job_detail_rule(decorated))
            if decorated_match != job:
                failures.append(f"{job}: decorated alias {decorated!r} resolves to {decorated_match!r}")

        if not rule.get("mainStat"):
            failures.append(f"{job}: mainStat missing")
        if not rule.get("attackType"):
            failures.append(f"{job}: attackType missing")
        if float(rule.get("weaponConstant") or 0) <= 0:
            failures.append(f"{job}: weaponConstant invalid")
        if float(rule.get("mastery") or 0) <= 0:
            failures.append(f"{job}: mastery invalid")

    if failures:
        raise AssertionError("\n".join(failures))


def assert_full_job_coverage() -> None:
    failures: list[str] = []
    for job in KMS_JOB_NAMES:
        coverage = calculation_coverage(job)
        current = coverage["current"]
        if not current["detailRuleApplied"]:
            failures.append(f"{job}: detail rule missing")
        if current["weaponConstant"] <= 0:
            failures.append(f"{job}: weapon constant missing")
        if current["mastery"] <= 0:
            failures.append(f"{job}: mastery missing")
        if current["jobConvertedMultiplier"] <= 0:
            failures.append(f"{job}: converted multiplier missing")
        if current["calibrationConfidence"] != "high":
            failures.append(f"{job}: calibration confidence missing")
        if not current["calibrationEvidence"]:
            failures.append(f"{job}: calibration evidence missing")
        if coverage["missingDetailJobs"]:
            failures.append(f"{job}: global detail missing {coverage['missingDetailJobs']}")
        if coverage["missingMultiplierJobs"]:
            failures.append(f"{job}: global multiplier missing {coverage['missingMultiplierJobs']}")
        if coverage["missingCombatJobs"]:
            failures.append(f"{job}: global combat missing {coverage['missingCombatJobs']}")
    if failures:
        raise AssertionError("\n".join(failures))


def assert_full_job_view_models() -> None:
    failures: list[str] = []
    for rule in JOB_DETAIL_RULES:
        job = str(rule["keywords"][0])
        main_stat = str(rule["mainStat"])
        attack_type = str(rule["attackType"])
        stat_mode = str(rule.get("statMode") or "single")
        if stat_mode == "demon_avenger":
            potential_line = "최대 HP : +3%"
        elif stat_mode == "xenon":
            potential_line = "STR : +3%"
        else:
            potential_line = f"{main_stat} : +3%"

        try:
            view = build_view_model(sample_raw(job, main_stat, attack_type, potential_line))
        except Exception as exc:  # pragma: no cover - assertion context
            failures.append(f"{job}: view model failed {type(exc).__name__}: {exc}")
            continue

        summary = view["summary"]
        primary = view["primaryMetric"]
        confidence = primary["confidence"]
        coverage = view["calculationCoverage"]["current"]
        formula = view["formulaDiagnostics"]
        plan = view["itemUpgradePlan"]
        manifest = view["jobFormulaManifest"]
        if confidence["score"] < 70:
            failures.append(f"{job}: primary metric confidence too low {confidence}")
        if not confidence["reasons"]:
            failures.append(f"{job}: primary metric confidence reasons missing")
        if primary["value"] != summary["unifiedConverted380"]:
            failures.append(f"{job}: primary metric does not match unified score")
        if primary["usedBy"]["bossBoard"] != primary["value"]:
            failures.append(f"{job}: boss board basis does not use primary metric")
        if primary["usedBy"]["itemUpgradePlan"] != primary["value"]:
            failures.append(f"{job}: item plan does not use primary metric")
        failures.extend(single_metric_failures(view, job))
        failures.extend(formula_integrity_failures(view, job))
        failures.extend(input_source_failures(view, job))
        failures.extend(readiness_failures(view, job, {"ready", "caution"}))
        failures.extend(formula_manifest_failures(manifest, job, job))
        if coverage["job"] != job:
            failures.append(f"{job}: matched job drifted to {coverage['job']}")
        if formula["status"] != "complete":
            failures.append(f"{job}: formula diagnostics incomplete {formula}")
        if not summary["jobRuleApplied"]:
            failures.append(f"{job}: job rule not applied")
        if summary["mainStat"] != main_stat:
            failures.append(f"{job}: main stat {summary['mainStat']} != {main_stat}")
        if summary["attackType"] != attack_type:
            failures.append(f"{job}: attack type {summary['attackType']} != {attack_type}")
        if summary["unifiedConverted380"] <= 0:
            failures.append(f"{job}: unified converted score missing")
        if summary["unifiedConverted380"] != summary["bossBasisConverted380"]:
            failures.append(f"{job}: boss basis is not unified converted score")
        if plan["basis"] != summary["unifiedBasis"]:
            failures.append(f"{job}: item plan basis mismatch")
        if plan["currentConverted"] != summary["unifiedConverted380"]:
            failures.append(f"{job}: item plan current score mismatch")
        failures.extend(recommendation_evidence_failures(plan, job))
        if not plan["top"]:
            failures.append(f"{job}: no item repair recommendations")
        for row in plan.get("top") or []:
            scenarios = row.get("scenarios") or []
            if not scenarios:
                failures.append(f"{job}/{row.get('name')}: scenarios missing")
                continue
            gains = [scenario["gain"] for scenario in scenarios]
            if gains != sorted(gains, reverse=True):
                failures.append(f"{job}/{row.get('name')}: scenarios not sorted {gains}")
            if row["expectedGain"] != scenarios[0]["gain"]:
                failures.append(f"{job}/{row.get('name')}: expected gain does not match first scenario")
            if row["expectedGainPercent"] <= 0 or scenarios[0]["gainPercent"] <= 0:
                failures.append(f"{job}/{row.get('name')}: gain percent missing")
            if row.get("scoreBasis") != plan["basis"]:
                failures.append(f"{job}/{row.get('name')}: score basis mismatch")
            if not scenarios[0].get("reason"):
                failures.append(f"{job}/{row.get('name')}: first scenario reason missing")
        if not plan["efficiencyProfile"]:
            failures.append(f"{job}: no upgrade efficiency profile")
        elif plan["primaryEfficiency"] != plan["efficiencyProfile"][0]:
            failures.append(f"{job}: primary efficiency does not match top efficiency")
        elif plan["primaryEfficiency"]["gain"] <= 0:
            failures.append(f"{job}: primary efficiency has no gain")
        if not plan["slotSummary"]:
            failures.append(f"{job}: no slot repair summary")
        if not plan["repairChecklist"]:
            failures.append(f"{job}: no repair checklist")
        elif not plan["repairChecklist"][0]["description"]:
            failures.append(f"{job}: repair checklist has no action description")
        reliability = plan.get("reliability") or {}
        if reliability.get("status") not in {"ready", "caution", "diagnostic", "blocked"}:
            failures.append(f"{job}: upgrade reliability status missing {reliability}")
        if not reliability.get("reasons"):
            failures.append(f"{job}: upgrade reliability reasons missing")
        if not view["bossBoard"]:
            failures.append(f"{job}: no boss board")
        if view["apiDataQuality"]["requiredPresent"] != 3:
            failures.append(f"{job}: required API diagnostics incomplete")

    if failures:
        raise AssertionError("\n".join(failures))


def assert_sample_view_model() -> None:
    raw = {
        "basic": {
            "character_name": "검증샘플",
            "world_name": "스카니아",
            "character_class": "레테",
            "character_level": 285,
            "character_image": "",
        },
        "stat": {
            "final_stat": [
                {"stat_name": "STR", "stat_value": "2000"},
                {"stat_name": "DEX", "stat_value": "2000"},
                {"stat_name": "INT", "stat_value": "7000"},
                {"stat_name": "LUK", "stat_value": "3000"},
                {"stat_name": "공격력", "stat_value": "1000"},
                {"stat_name": "마력", "stat_value": "5000"},
                {"stat_name": "데미지", "stat_value": "90"},
                {"stat_name": "보스 몬스터 데미지", "stat_value": "450"},
                {"stat_name": "최종 데미지", "stat_value": "60"},
                {"stat_name": "방어율 무시", "stat_value": "97"},
                {"stat_name": "크리티컬 확률", "stat_value": "100"},
                {"stat_name": "크리티컬 데미지", "stat_value": "100"},
                {"stat_name": "전투력", "stat_value": "400000000"},
            ]
        },
        "itemEquipment": {
            "item_equipment": [
                {
                    "item_equipment_slot": "무기",
                    "item_equipment_part": "샤이닝 로드",
                    "item_name": "검증 무기",
                    "item_icon": "",
                    "starforce": "17",
                    "potential_option_grade": "레전드리",
                    "potential_option_1": "마력 : +9%",
                    "potential_option_2": "보스 몬스터 공격 시 데미지 : +30%",
                    "additional_potential_option_1": "마력 : +3",
                    "item_total_option": {"magic_power": "320", "int": "80"},
                    "item_base_option": {"magic_power": "200"},
                },
                {
                    "item_equipment_slot": "모자",
                    "item_equipment_part": "모자",
                    "item_name": "검증 모자",
                    "item_icon": "",
                    "starforce": "17",
                    "potential_option_grade": "유니크",
                    "potential_option_1": "INT : +9%",
                    "additional_potential_option_1": "마력 : +3",
                    "item_total_option": {"int": "140", "magic_power": "20"},
                    "item_base_option": {"int": "30"},
                },
            ]
        },
        "otherStat": {
            "character_other_stat": [
                {"stat_name": "검증 기타", "stat_value": "+1"},
            ]
        },
        "hexamatrixStat": {
            "character_hexa_stat_core": [
                {
                    "main_stat_name": "주력 스탯",
                    "main_stat_level": 5,
                    "sub_stat_name_1": "마력",
                    "sub_stat_level_1": 3,
                    "sub_stat_name_2": "보스 데미지",
                    "sub_stat_level_2": 2,
                }
            ]
        },
        "hexamatrix": {
            "character_hexa_core_equipment": [
                {"hexa_core_name": "검증 HEXA 코어", "hexa_core_level": 30},
            ]
        },
        "skill6": {
            "character_skill": [
                {"skill_name": "검증 6차 스킬", "skill_level": 20},
            ]
        },
    }
    view = build_view_model(raw)
    coverage = view["calculationCoverage"]
    api_quality = view["apiDataQuality"]
    primary = view["primaryMetric"]
    confidence = primary["confidence"]
    assert api_quality["requiredPresent"] == 3
    assert api_quality["requiredTotal"] == 3
    assert api_quality["missingRequiredSections"] == []
    assert "otherStat" in api_quality["presentSections"]
    assert api_quality["warningCount"] == 0
    assert view["extra"]["counts"]["otherStats"] == 1
    assert view["extra"]["otherStats"][0]["name"] == "검증 기타"
    assert view["summary"]["apiQualityPercent"] == api_quality["qualityPercent"]
    assert view["summary"]["apiWarningCount"] == api_quality["warningCount"]
    assert view["summary"]["formulaStatus"] == "complete"
    assert view["formulaDiagnostics"]["matchedJob"] == "레테"
    assert view["formulaDiagnostics"]["knownJobsCovered"]
    assert primary["id"] == "unifiedConverted380"
    assert primary["label"] == "대표 환산(380)"
    assert primary["value"] == view["summary"]["unifiedConverted380"]
    assert primary["usedBy"]["bossBoard"] == primary["value"]
    assert primary["usedBy"]["itemUpgradePlan"] == primary["value"]
    assert primary["usedBy"]["presetOptimization"] == primary["value"]
    assert primary["comparison"]["hexaConverted380"] == primary["value"]
    single_metric_problems = single_metric_failures(view, "sample 레테")
    assert not single_metric_problems, "\n".join(single_metric_problems)
    assert view["hexaConvertedDetail"]["skillEffect"]["totalLevel"] == 50
    assert view["hexaConvertedDetail"]["completionRatio"] < 1
    assert view["hexaConvertedDetail"]["statConvertedGain"] > 0
    assert view["summary"]["hexaStatGain380"] == round(view["hexaConvertedDetail"]["statConvertedGain"])
    assert view["summary"]["hexaStatGainPercent"] > 0
    assert confidence["score"] >= 70
    assert confidence["level"] in {"high", "medium"}
    assert confidence["reasons"]
    assert coverage["targetJobs"] >= 48
    assert coverage["current"]["job"] == "레테"
    assert view["jobFormulaManifest"]["current"]["job"] == "레테"
    assert view["jobFormulaManifest"]["current"]["mainStat"] == "INT"
    assert view["jobFormulaManifest"]["current"]["attackType"] == "마력"
    assert not formula_manifest_failures(view["jobFormulaManifest"], "sample 레테", "레테")
    assert view["summary"]["mainStat"] == "INT"
    assert view["summary"]["attackType"] == "마력"
    assert view["summary"]["unifiedConverted380"] == view["summary"]["bossBasisConverted380"]
    assert view["summary"]["unifiedBasis"] == view["itemUpgradePlan"]["basis"]
    assert view["itemUpgradePlan"]["currentConverted"] == view["summary"]["unifiedConverted380"]
    assert view["bossBoard"][0]["currentConverted"] == view["summary"]["unifiedConverted380"]
    assert view["itemUpgradePlan"]["top"]
    assert view["itemUpgradePlan"]["top"][0]["priorityScore"] > 0
    assert view["itemUpgradePlan"]["top"][0]["weaknesses"]
    assert not recommendation_evidence_failures(view["itemUpgradePlan"], "sample 레테")
    assert view["itemUpgradePlan"]["repairEvidence"]["top"]["item"] == view["itemUpgradePlan"]["top"][0]["name"]
    assert view["itemUpgradePlan"]["repairAudit"]["allPassed"]
    assert view["itemUpgradePlan"]["repairAudit"]["topItem"] == view["itemUpgradePlan"]["top"][0]["name"]
    assert view["itemUpgradePlan"]["top"][0]["scoreBasis"] == view["itemUpgradePlan"]["basis"]
    assert view["itemUpgradePlan"]["top"][0]["expectedGain"] == view["itemUpgradePlan"]["top"][0]["scenarios"][0]["gain"]
    assert view["itemUpgradePlan"]["top"][0]["scenarios"][0]["gainPercent"] > 0
    assert view["itemUpgradePlan"]["top"][0]["scenarios"][0]["reason"]
    assert view["itemUpgradePlan"]["efficiencyProfile"]
    assert view["itemUpgradePlan"]["primaryEfficiency"] == view["itemUpgradePlan"]["efficiencyProfile"][0]
    assert view["itemUpgradePlan"]["primaryEfficiency"]["gain"] > 0
    assert view["itemUpgradePlan"]["primaryEfficiency"]["gainPercent"] > 0
    assert view["itemUpgradePlan"]["categorySummary"]
    assert view["itemUpgradePlan"]["primaryCategory"]["totalGain"] > 0
    assert view["itemUpgradePlan"]["weaknessSummary"]
    assert view["itemUpgradePlan"]["primaryWeakness"] == view["itemUpgradePlan"]["weaknessSummary"][0]
    assert view["itemUpgradePlan"]["primaryWeakness"]["candidateCount"] > 0
    assert view["itemUpgradePlan"]["slotSummary"]
    assert view["itemUpgradePlan"]["primarySlot"]["totalGain"] > 0
    assert view["itemUpgradePlan"]["repairFocus"]["slot"]
    assert view["itemUpgradePlan"]["repairFocus"]["description"]
    assert view["itemUpgradePlan"]["repairChecklist"]
    assert view["itemUpgradePlan"]["repairChecklist"][0]["rank"] == 1
    assert view["itemUpgradePlan"]["repairChecklist"][0]["expectedGain"] > 0
    assert view["itemUpgradePlan"]["repairRoadmap"]
    assert view["itemUpgradePlan"]["repairRoadmap"][0]["projectedConverted"] > view["itemUpgradePlan"]["currentConverted"]
    assert view["itemUpgradePlan"]["roadmapSummary"]["projectedConverted"] >= view["itemUpgradePlan"]["repairRoadmap"][0]["projectedConverted"]
    assert view["itemUpgradePlan"]["reliability"]["status"] in {"caution", "ready"}
    assert view["itemUpgradePlan"]["reliability"]["score"] == view["primaryMetric"]["confidence"]["score"]
    assert view["itemUpgradePlan"]["reliability"]["reasons"]
    assert view["calculationAudit"]["rows"]
    assert view["calculationAudit"]["unifiedConverted"] == view["summary"]["unifiedConverted380"]
    assert not formula_integrity_failures(view, "sample 레테")
    assert view["formulaIntegrityAudit"]["allPassed"]
    assert not input_source_failures(view, "sample 레테")
    assert view["inputSourceAudit"]["allRequiredPresent"]
    assert not readiness_failures(view, "sample 레테", {"ready", "caution"})
    assert view["readinessAudit"]["passedCount"] >= 6
    assert view["singleMetricAudit"]["allMatched"]
    assert view["singleMetricAudit"]["value"] == view["summary"]["unifiedConverted380"]
    assert any(row["label"] == "직업 샘플 배율" for row in view["calculationAudit"]["rows"])
    assert any(row["label"] == "보정 표본" for row in view["calculationAudit"]["rows"])
    assert any(row["label"] == "최종 상세 배율" for row in view["calculationAudit"]["rows"])


def sample_raw(character_class: str, main_stat: str, attack_type: str, potential_line: str) -> dict:
    return {
        "basic": {
            "character_name": f"{character_class}샘플",
            "world_name": "스카니아",
            "character_class": character_class,
            "character_level": 285,
            "character_image": "",
        },
        "stat": {
            "final_stat": [
                {"stat_name": "STR", "stat_value": "7000"},
                {"stat_name": "DEX", "stat_value": "6500"},
                {"stat_name": "INT", "stat_value": "7000"},
                {"stat_name": "LUK", "stat_value": "6200"},
                {"stat_name": "최대 HP", "stat_value": "500000"},
                {"stat_name": "공격력", "stat_value": "5000"},
                {"stat_name": "마력", "stat_value": "5000"},
                {"stat_name": "데미지", "stat_value": "90"},
                {"stat_name": "보스 몬스터 데미지", "stat_value": "450"},
                {"stat_name": "최종 데미지", "stat_value": "60"},
                {"stat_name": "방어율 무시", "stat_value": "97"},
                {"stat_name": "크리티컬 확률", "stat_value": "100"},
                {"stat_name": "크리티컬 데미지", "stat_value": "100"},
                {"stat_name": "전투력", "stat_value": "400000000"},
            ]
        },
        "itemEquipment": {
            "item_equipment": [
                {
                    "item_equipment_slot": "무기",
                    "item_equipment_part": "샤이닝 로드" if attack_type == "마력" else "에너지소드",
                    "item_name": "검증 무기",
                    "item_icon": "",
                    "starforce": "17",
                    "potential_option_grade": "유니크",
                    "potential_option_1": f"{attack_type} : +3%",
                    "potential_option_2": "보스 몬스터 공격 시 데미지 : +10%",
                    "additional_potential_option_1": f"{attack_type} : +1",
                    "item_total_option": {"attack_power": "320", "magic_power": "320", "str": "80", "int": "80"},
                    "item_base_option": {"attack_power": "200", "magic_power": "200"},
                    "item_add_option": {"attack_power": "30", "magic_power": "30"},
                    "item_etc_option": {"attack_power": "20", "magic_power": "20"},
                },
                {
                    "item_equipment_slot": "모자",
                    "item_equipment_part": "모자",
                    "item_name": "검증 모자",
                    "item_icon": "",
                    "starforce": "17",
                    "potential_option_grade": "유니크",
                    "potential_option_1": potential_line,
                    "additional_potential_option_1": f"{attack_type} : +1",
                    "item_total_option": {"str": "140", "dex": "140", "int": "140", "luk": "140", "max_hp": "5000", "attack_power": "20", "magic_power": "20"},
                    "item_base_option": {main_stat.lower(): "30"},
                    "item_add_option": {"str": "40", "dex": "40", "int": "40", "luk": "40", "max_hp": "1200"},
                    "item_etc_option": {"str": "30", "dex": "30", "int": "30", "luk": "30", "max_hp": "900"},
                },
            ]
        },
    }


def assert_special_item_targets() -> None:
    demon = build_view_model(sample_raw("데몬어벤져", "STR", "공격력", "최대 HP : +3%"))
    demon_plan = demon["itemUpgradePlan"]
    assert demon["calculationCoverage"]["current"]["statMode"] == "demon_avenger"
    assert demon_plan["upgradeTargets"] == ["최대 HP"]
    assert demon_plan["efficiencyProfile"]
    assert any("HP" in row["action"] for row in demon_plan["efficiencyProfile"])
    assert any("HP" in row["recommendedAction"] for row in demon_plan["top"])
    assert any("HP" in weakness["label"] for row in demon_plan["top"] for weakness in row["weaknesses"])
    assert any("HP" in row["label"] for row in demon_plan["weaknessSummary"])
    assert any(("추옵" in weakness["label"] or "작" in weakness["label"]) for row in demon_plan["top"] for weakness in row["weaknesses"])
    assert demon_plan["categorySummary"]
    assert demon_plan["weaknessSummary"]
    assert demon_plan["slotSummary"]

    xenon = build_view_model(sample_raw("제논", "LUK", "공격력", "STR : +3%"))
    xenon_plan = xenon["itemUpgradePlan"]
    assert xenon["calculationCoverage"]["current"]["statMode"] == "xenon"
    assert xenon_plan["upgradeTargets"] == ["STR", "DEX", "LUK"]
    assert xenon_plan["efficiencyProfile"]
    assert any("STR/DEX/LUK" in row["action"] for row in xenon_plan["efficiencyProfile"])
    assert any("STR/DEX/LUK" in row["recommendedAction"] for row in xenon_plan["top"])
    assert any("STR/DEX/LUK" in weakness["label"] for row in xenon_plan["top"] for weakness in row["weaknesses"])
    assert any("STR/DEX/LUK" in row["label"] for row in xenon_plan["weaknessSummary"])
    assert any(("추옵" in scenario["type"] or "작" in scenario["type"]) for row in xenon_plan["top"] for scenario in row["scenarios"])
    assert xenon_plan["categorySummary"]
    assert xenon_plan["weaknessSummary"]
    assert xenon_plan["slotSummary"]


def assert_preset_metric_basis() -> None:
    raw = sample_raw("레테", "INT", "마력", "INT : +3%")
    raw["itemEquipment"]["preset_no"] = 1
    raw["itemEquipment"]["item_equipment_preset_1"] = raw["itemEquipment"]["item_equipment"]
    second_items = [dict(item) for item in raw["itemEquipment"]["item_equipment"]]
    second_items[0]["potential_option_1"] = "마력 : +12%"
    raw["itemEquipment"]["item_equipment_preset_2"] = second_items
    view = build_view_model(raw)
    assert view["presetOptimization"]["basis"] == view["summary"]["unifiedBasis"]
    assert view["presetOptimization"]["current"]["converted"] == view["summary"]["unifiedConverted380"]
    assert not single_metric_failures(view, "preset 레테")
    current_combo = next(row for row in view["presetViews"]["combinations"] if row["itemPreset"] == 1)
    assert current_combo["converted"] == view["summary"]["unifiedConverted380"]
    assert view["apiDataQuality"]["presetSections"]["itemPresetCount"] >= 2
    assert view["presetUpgradePlans"]
    assert len(view["presetUpgradePlans"]) >= 2
    current_plan = next(row for row in view["presetUpgradePlans"] if row["isCurrent"])
    assert current_plan["converted"] == view["summary"]["unifiedConverted380"]
    assert current_plan["plan"]["basis"] == view["summary"]["unifiedBasis"]
    assert current_plan["plan"]["reliability"]["status"] in {"caution", "ready"}
    assert current_plan["plan"]["presetSelection"] == {
        "itemPreset": current_plan["itemPreset"],
        "abilityPreset": current_plan["abilityPreset"],
        "hyperPreset": current_plan["hyperPreset"],
        "isCurrent": True,
    }
    assert current_plan["plan"]["slotSummary"]
    assert not recommendation_evidence_failures(current_plan["plan"], "current preset 레테")
    second_plan = next(row for row in view["presetUpgradePlans"] if row["itemPreset"] == 2)
    assert second_plan["plan"]["presetSelection"]["itemPreset"] == 2
    assert second_plan["plan"]["presetSelection"]["abilityPreset"] == second_plan["abilityPreset"]
    assert second_plan["plan"]["presetSelection"]["hyperPreset"] == second_plan["hyperPreset"]
    assert second_plan["plan"]["reliability"]["score"] == view["primaryMetric"]["confidence"]["score"]
    assert second_plan["plan"]["slotSummary"]
    assert not recommendation_evidence_failures(second_plan["plan"], "second preset 레테")


def assert_api_warning_diagnostics() -> None:
    raw = sample_raw("레테", "INT", "마력", "INT : +3%")
    raw["warnings"] = [{"section": "vmatrix", "message": "sample warning"}]
    view = build_view_model(raw)
    quality = view["apiDataQuality"]
    assert quality["status"] == "warning"
    assert quality["warningCount"] == 1
    assert quality["warningSections"] == ["vmatrix"]
    assert quality["warnings"][0]["message"] == "sample warning"
    assert quality["missingRequiredSections"] == []
    assert "vmatrix" in quality["missingOptionalSections"]
    assert view["summary"]["apiWarningCount"] == 1
    assert view["primaryMetric"]["confidence"]["score"] < 90
    assert any("경고" in reason for reason in view["primaryMetric"]["confidence"]["reasons"])
    assert view["inputSourceAudit"]["allRequiredPresent"]
    assert view["inputSourceAudit"]["warningCount"] >= 1
    assert any("vmatrix" in row.get("warningSections", []) for row in view["inputSourceAudit"]["rows"])
    assert not readiness_failures(view, "warning 레테", {"caution", "diagnostic"})
    assert view["itemUpgradePlan"]["reliability"]["status"] == "caution"
    assert any("경고" in reason for reason in view["itemUpgradePlan"]["reliability"]["reasons"])


def assert_unknown_job_formula_diagnostics() -> None:
    view = build_view_model(sample_raw("신규직업", "INT", "마력", "INT : +3%"))
    formula = view["formulaDiagnostics"]
    manifest = view["jobFormulaManifest"]
    assert formula["status"] == "fallback"
    assert not formula["detailRuleApplied"]
    assert not formula["convertedMultiplierApplied"]
    assert "직업 상세식" in formula["missingTables"]
    assert manifest["current"]["job"] == "신규직업"
    assert manifest["current"]["statMode"] == "fallback"
    assert not manifest["current"]["matched"]
    assert not formula_manifest_failures(manifest, "unknown manifest")
    assert view["summary"]["formulaStatus"] == "fallback"
    assert view["summary"]["unifiedConverted380"] > 0
    assert view["itemUpgradePlan"]["repairChecklist"]
    assert view["primaryMetric"]["confidence"]["level"] in {"low", "critical"}
    assert any("미지원" in reason for reason in view["primaryMetric"]["confidence"]["reasons"])
    assert not readiness_failures(view, "unknown job", {"diagnostic"})


def assert_option_line_parsing() -> None:
    profile = profile_from_lines(
        [
            "공격력 및 마력 : +9%",
            "보공 +40%",
            "몬스터방어율무시 : +35%",
            "크뎀 : +8%",
            "크확 : +12%",
            "최종뎀 : +1%",
            "데미지 : +12%",
            "일반 몬스터 공격 시 데미지 : +7%",
            "전체스탯 : +5%",
        ]
    )
    assert profile["percent"][K_ATTACK] == 9
    assert profile["percent"][K_MAGIC] == 9
    assert profile["combat"][K_BOSS] == 40
    assert profile["combat"][K_IED] == 35
    assert profile["combat"][K_CRIT_DAMAGE] == 8
    assert profile["combat"][K_CRIT_RATE] == 12
    assert profile["combat"][K_FINAL] == 1
    assert profile["combat"][K_DAMAGE] == 12
    assert all(profile["percent"][stat] == 5 for stat in ("STR", "DEX", "INT", "LUK"))


def main() -> None:
    assert_job_table_integrity()
    assert_full_job_coverage()
    assert_full_job_view_models()
    assert_sample_view_model()
    assert_special_item_targets()
    assert_preset_metric_basis()
    assert_api_warning_diagnostics()
    assert_unknown_job_formula_diagnostics()
    assert_option_line_parsing()
    print(f"OK: {len(KMS_JOB_NAMES)} KMS jobs covered")


if __name__ == "__main__":
    main()
