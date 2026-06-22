from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.calc import KMS_JOB_NAMES, build_view_model, calculation_coverage  # noqa: E402


def assert_full_job_coverage() -> None:
    failures: list[str] = []
    for job in KMS_JOB_NAMES:
        coverage = calculation_coverage(job)
        current = coverage["current"]
        if not current["detailRuleApplied"]:
            failures.append(f"{job}: detail rule missing")
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

    xenon = build_view_model(sample_raw("제논", "LUK", "공격력", "STR : +3%"))
    xenon_plan = xenon["itemUpgradePlan"]
    assert xenon["calculationCoverage"]["current"]["statMode"] == "xenon"
    assert xenon_plan["upgradeTargets"] == ["STR", "DEX", "LUK"]
    assert any("STR/DEX/LUK" in row["recommendedAction"] for row in xenon_plan["top"])
    assert any("STR/DEX/LUK" in weakness["label"] for row in xenon_plan["top"] for weakness in row["weaknesses"])
    assert any(("추옵" in scenario["type"] or "작" in scenario["type"]) for row in xenon_plan["top"] for scenario in row["scenarios"])
    assert xenon_plan["categorySummary"]


def assert_preset_metric_basis() -> None:
    raw = sample_raw("레테", "INT", "마력", "INT : +3%")
    raw["itemEquipment"]["preset_no"] = 1
    raw["itemEquipment"]["item_equipment_preset_1"] = raw["itemEquipment"]["item_equipment"]
    view = build_view_model(raw)
    assert view["presetOptimization"]["basis"] == view["summary"]["unifiedBasis"]
    assert view["presetOptimization"]["current"]["converted"] == view["summary"]["unifiedConverted380"]
    assert view["presetViews"]["combinations"][0]["converted"] == view["summary"]["unifiedConverted380"]


def main() -> None:
    assert_full_job_coverage()
    assert_sample_view_model()
    assert_special_item_targets()
    assert_preset_metric_basis()
    print(f"OK: {len(KMS_JOB_NAMES)} KMS jobs covered")


if __name__ == "__main__":
    main()
