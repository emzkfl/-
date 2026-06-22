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
    job_detail_rule,
    primary_job_name,
)


def table_jobs(rows: list[dict] | tuple[dict, ...]) -> set[str]:
    return {str(row["keywords"][0]) for row in rows}


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
    assert view["summary"]["mainStat"] == "INT"
    assert view["summary"]["attackType"] == "마력"
    assert view["summary"]["unifiedConverted380"] == view["summary"]["bossBasisConverted380"]
    assert view["summary"]["unifiedBasis"] == view["itemUpgradePlan"]["basis"]
    assert view["itemUpgradePlan"]["currentConverted"] == view["summary"]["unifiedConverted380"]
    assert view["bossBoard"][0]["currentConverted"] == view["summary"]["unifiedConverted380"]
    assert view["itemUpgradePlan"]["top"]
    assert view["itemUpgradePlan"]["top"][0]["priorityScore"] > 0
    assert view["itemUpgradePlan"]["top"][0]["weaknesses"]
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
    assert view["itemUpgradePlan"]["slotSummary"]
    assert view["itemUpgradePlan"]["primarySlot"]["totalGain"] > 0
    assert view["itemUpgradePlan"]["repairFocus"]["slot"]
    assert view["itemUpgradePlan"]["repairFocus"]["description"]
    assert view["itemUpgradePlan"]["repairChecklist"]
    assert view["itemUpgradePlan"]["repairChecklist"][0]["rank"] == 1
    assert view["itemUpgradePlan"]["repairChecklist"][0]["expectedGain"] > 0
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
    assert demon_plan["efficiencyProfile"]
    assert any("HP" in row["action"] for row in demon_plan["efficiencyProfile"])
    assert any("HP" in row["recommendedAction"] for row in demon_plan["top"])
    assert any("HP" in weakness["label"] for row in demon_plan["top"] for weakness in row["weaknesses"])
    assert any(("추옵" in weakness["label"] or "작" in weakness["label"]) for row in demon_plan["top"] for weakness in row["weaknesses"])
    assert demon_plan["categorySummary"]
    assert demon_plan["slotSummary"]

    xenon = build_view_model(sample_raw("제논", "LUK", "공격력", "STR : +3%"))
    xenon_plan = xenon["itemUpgradePlan"]
    assert xenon["calculationCoverage"]["current"]["statMode"] == "xenon"
    assert xenon_plan["upgradeTargets"] == ["STR", "DEX", "LUK"]
    assert xenon_plan["efficiencyProfile"]
    assert any("STR/DEX/LUK" in row["action"] for row in xenon_plan["efficiencyProfile"])
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
    assert current_plan["plan"]["presetSelection"] == {
        "itemPreset": current_plan["itemPreset"],
        "abilityPreset": current_plan["abilityPreset"],
        "hyperPreset": current_plan["hyperPreset"],
        "isCurrent": True,
    }
    assert current_plan["plan"]["slotSummary"]
    second_plan = next(row for row in view["presetUpgradePlans"] if row["itemPreset"] == 2)
    assert second_plan["plan"]["presetSelection"]["itemPreset"] == 2
    assert second_plan["plan"]["presetSelection"]["abilityPreset"] == second_plan["abilityPreset"]
    assert second_plan["plan"]["presetSelection"]["hyperPreset"] == second_plan["hyperPreset"]
    assert second_plan["plan"]["slotSummary"]


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


def assert_unknown_job_formula_diagnostics() -> None:
    view = build_view_model(sample_raw("신규직업", "INT", "마력", "INT : +3%"))
    formula = view["formulaDiagnostics"]
    assert formula["status"] == "fallback"
    assert not formula["detailRuleApplied"]
    assert not formula["convertedMultiplierApplied"]
    assert "직업 상세식" in formula["missingTables"]
    assert view["summary"]["formulaStatus"] == "fallback"
    assert view["summary"]["unifiedConverted380"] > 0
    assert view["itemUpgradePlan"]["repairChecklist"]
    assert view["primaryMetric"]["confidence"]["level"] in {"low", "critical"}
    assert any("미지원" in reason for reason in view["primaryMetric"]["confidence"]["reasons"])


def main() -> None:
    assert_job_table_integrity()
    assert_full_job_coverage()
    assert_full_job_view_models()
    assert_sample_view_model()
    assert_special_item_targets()
    assert_preset_metric_basis()
    assert_api_warning_diagnostics()
    assert_unknown_job_formula_diagnostics()
    print(f"OK: {len(KMS_JOB_NAMES)} KMS jobs covered")


if __name__ == "__main__":
    main()
