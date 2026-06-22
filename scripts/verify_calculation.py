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
    KMS_JOB_NAMES,
    SPECIAL_COMBAT_CONVERTED_MODELS,
    build_view_model,
    calculation_coverage,
)


def table_jobs(rows: list[dict] | tuple[dict, ...]) -> set[str]:
    return {str(row["keywords"][0]) for row in rows}


def assert_job_table_integrity() -> None:
    failures: list[str] = []
    job_set = set(KMS_JOB_NAMES)
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

    for rule in JOB_DETAIL_RULES:
        job = str(rule["keywords"][0])
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
    }
    view = build_view_model(raw)
    coverage = view["calculationCoverage"]
    api_quality = view["apiDataQuality"]
    assert api_quality["requiredPresent"] == 3
    assert api_quality["requiredTotal"] == 3
    assert api_quality["missingRequiredSections"] == []
    assert api_quality["warningCount"] == 0
    assert view["summary"]["apiQualityPercent"] == api_quality["qualityPercent"]
    assert view["summary"]["apiWarningCount"] == api_quality["warningCount"]
    assert coverage["targetJobs"] >= 48
    assert coverage["current"]["job"] == "레테"
    assert view["summary"]["mainStat"] == "INT"
    assert view["summary"]["attackType"] == "마력"
    assert view["summary"]["unifiedConverted380"] == view["summary"]["bossBasisConverted380"]
    assert view["summary"]["unifiedBasis"] == view["itemUpgradePlan"]["basis"]
    assert view["itemUpgradePlan"]["currentConverted"] == view["summary"]["unifiedConverted380"]
    assert view["bossBoard"][0]["currentConverted"] == view["summary"]["unifiedConverted380"]
    assert view["itemUpgradePlan"]["top"]
    assert view["itemUpgradePlan"]["top"][0]["priorityScore"] > 0
    assert view["itemUpgradePlan"]["top"][0]["weaknesses"]
    assert view["itemUpgradePlan"]["categorySummary"]
    assert view["itemUpgradePlan"]["primaryCategory"]["totalGain"] > 0
    assert view["itemUpgradePlan"]["slotSummary"]
    assert view["itemUpgradePlan"]["primarySlot"]["totalGain"] > 0
    assert view["itemUpgradePlan"]["repairFocus"]["slot"]
    assert view["calculationAudit"]["rows"]
    assert view["calculationAudit"]["unifiedConverted"] == view["summary"]["unifiedConverted380"]
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
    assert any("HP" in row["recommendedAction"] for row in demon_plan["top"])
    assert any("HP" in weakness["label"] for row in demon_plan["top"] for weakness in row["weaknesses"])
    assert any(("추옵" in weakness["label"] or "작" in weakness["label"]) for row in demon_plan["top"] for weakness in row["weaknesses"])
    assert demon_plan["categorySummary"]
    assert demon_plan["slotSummary"]

    xenon = build_view_model(sample_raw("제논", "LUK", "공격력", "STR : +3%"))
    xenon_plan = xenon["itemUpgradePlan"]
    assert xenon["calculationCoverage"]["current"]["statMode"] == "xenon"
    assert xenon_plan["upgradeTargets"] == ["STR", "DEX", "LUK"]
    assert any("STR/DEX/LUK" in row["recommendedAction"] for row in xenon_plan["top"])
    assert any("STR/DEX/LUK" in weakness["label"] for row in xenon_plan["top"] for weakness in row["weaknesses"])
    assert any(("추옵" in scenario["type"] or "작" in scenario["type"]) for row in xenon_plan["top"] for scenario in row["scenarios"])
    assert xenon_plan["categorySummary"]
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
    current_combo = next(row for row in view["presetViews"]["combinations"] if row["itemPreset"] == 1)
    assert current_combo["converted"] == view["summary"]["unifiedConverted380"]
    assert view["apiDataQuality"]["presetSections"]["itemPresetCount"] >= 2
    assert view["presetUpgradePlans"]
    assert len(view["presetUpgradePlans"]) >= 2
    current_plan = next(row for row in view["presetUpgradePlans"] if row["isCurrent"])
    assert current_plan["converted"] == view["summary"]["unifiedConverted380"]
    assert current_plan["plan"]["basis"] == view["summary"]["unifiedBasis"]
    assert current_plan["plan"]["slotSummary"]
    assert any(row["itemPreset"] == 2 and row["plan"]["slotSummary"] for row in view["presetUpgradePlans"])


def main() -> None:
    assert_job_table_integrity()
    assert_full_job_coverage()
    assert_sample_view_model()
    assert_special_item_targets()
    assert_preset_metric_basis()
    print(f"OK: {len(KMS_JOB_NAMES)} KMS jobs covered")


if __name__ == "__main__":
    main()
