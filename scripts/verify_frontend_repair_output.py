from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

INDEX = ROOT / "app" / "static" / "index.html"
APP_JS = ROOT / "app" / "static" / "app.js"


REQUIRED_INDEX_MARKERS = {
    "upgrade-summary": "summary target",
    "upgrade-slot-list": "slot/checklist target",
    "upgrade-category-list": "weakness/category target",
    "upgrade-list": "item recommendation target",
    "개선 우선순위": "visible repair section title",
}

REQUIRED_RENDER_MARKERS = {
    "selectedUpgradePlan(data)": "selected preset repair plan",
    "data.goalContract": "goal contract source",
    "goal.canRecommendItems": "goal contract recommendation gate",
    "goalText": "goal contract summary text",
    "plan.repairFocus": "primary repair focus",
    "plan.repairChecklist": "ranked repair checklist",
    "plan.repairRoadmap": "projected repair roadmap",
    "plan.roadmapSummary": "roadmap summary",
    "plan.repairAudit": "repair audit",
    "plan.reliability": "repair reliability",
    "plan.slotSummary": "slot summary",
    "plan.weaknessSummary": "weakness summary",
    "plan.categorySummary": "category summary",
    "plan.efficiencyProfile": "efficiency profile",
    "row.slot": "item slot",
    "row.name": "item name",
    "row.currentState": "current item state",
    "row.recommendedType": "recommended option type",
    "row.recommendedAction": "recommended action",
    "row.reason": "recommendation reason",
    "row.expectedGain": "expected converted gain",
    "row.expectedGainPercent": "expected gain percent",
    "row.contribution": "current item contribution",
    "row.priorityScore": "priority score",
    "row.potentialSummary": "potential summary",
    "row.additionalPotentialSummary": "additional potential summary",
    "row.recommendationEvidence": "recommendation evidence",
    "row.scenarios": "improvement scenarios",
    "row.weaknesses": "weakness details",
    "evidence.weaknessLabel": "evidence weakness label",
    "evidence.weightedContribution": "evidence weighted contribution",
    "weakness.current": "weakness current value",
    "weakness.target": "weakness target value",
    "weakness.gap": "weakness gap",
    "scenario.action": "scenario action",
    "scenario.gain": "scenario gain",
    "추천할 개선 항목이 없습니다": "empty repair state",
}


def function_body(source: str, function_name: str, next_function_name: str) -> str:
    start = source.find(f"function {function_name}")
    end = source.find(f"function {next_function_name}", start)
    if start < 0 or end < 0:
        raise AssertionError(f"could not locate {function_name} body")
    return source[start:end]


def assert_frontend_repair_output() -> None:
    index = INDEX.read_text(encoding="utf-8")
    app_js = APP_JS.read_text(encoding="utf-8")
    render_upgrade = function_body(app_js, "renderUpgradePlan", "renderItems")
    failures: list[str] = []

    for path, text in ((INDEX, index), (APP_JS, app_js)):
        if "\ufffd" in text:
            failures.append(f"{path}: contains replacement characters")

    for marker, label in REQUIRED_INDEX_MARKERS.items():
        if marker not in index:
            failures.append(f"index: missing {label} marker {marker!r}")

    for marker, label in REQUIRED_RENDER_MARKERS.items():
        if marker not in render_upgrade:
            failures.append(f"renderUpgradePlan: missing {label} marker {marker!r}")

    if "upgradeSummary.textContent" not in render_upgrade:
        failures.append("renderUpgradePlan: summary text is not populated")
    if "upgradeSlotList.innerHTML" not in render_upgrade:
        failures.append("renderUpgradePlan: slot/checklist list is not populated")
    if "upgradeCategoryList.innerHTML" not in render_upgrade:
        failures.append("renderUpgradePlan: weakness/category list is not populated")
    if "upgradeList.innerHTML" not in render_upgrade:
        failures.append("renderUpgradePlan: item recommendation list is not populated")
    if "plan.currentConverted" not in render_upgrade or "primary.value" not in render_upgrade:
        failures.append("renderUpgradePlan: current representative metric is not shown")

    if failures:
        raise AssertionError("\n".join(failures))


def main() -> None:
    assert_frontend_repair_output()
    print("OK: frontend renders item repair targets and evidence fields")


if __name__ == "__main__":
    main()
