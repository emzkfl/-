from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


INDEX = ROOT / "app" / "static" / "index.html"
APP_JS = ROOT / "app" / "static" / "app.js"


def function_body(source: str, function_name: str, next_function_name: str) -> str:
    start = source.find(f"function {function_name}")
    end = source.find(f"function {next_function_name}", start)
    if start < 0 or end < 0:
        raise AssertionError(f"could not locate {function_name} body")
    return source[start:end]


def assert_frontend_single_metric() -> None:
    index = INDEX.read_text(encoding="utf-8")
    app_js = APP_JS.read_text(encoding="utf-8")
    failures: list[str] = []

    for path, text in ((INDEX, index), (APP_JS, app_js)):
        if "\ufffd" in text:
            failures.append(f"{path}: contains replacement characters")

    if index.count("대표 환산 (380)") != 1:
        failures.append("index: 대표 환산 card must appear exactly once")
    if "헥사환산 (380)" in index:
        failures.append("index: HEXA converted must not be shown as a second top-level metric")
    if "지표 신뢰도" not in index:
        failures.append("index: metric confidence card missing")
    if "#metric-confidence" not in app_js or "#metric-detail" not in app_js:
        failures.append("app.js: metric confidence/detail selectors missing")
    if "#hexa-power" in app_js or "#hexa-detail" in app_js:
        failures.append("app.js: legacy HEXA score selectors still used")
    if "hexaPower.textContent" in app_js or "hexaDetail.textContent" in app_js:
        failures.append("app.js: legacy HEXA score rendering still used")
    if "metricConfidence.textContent" not in app_js:
        failures.append("app.js: confidence score is not rendered")
    if "보스·프리셋·아이템 개선" not in app_js:
        failures.append("app.js: single-metric usage explanation missing")
    if "data.goalContract" not in app_js:
        failures.append("app.js: goal contract response is not consumed")
    if "목표 계약" not in app_js:
        failures.append("app.js: goal contract status is not visible in coverage")

    render_scores = function_body(app_js, "renderScores", "presetByNo")
    render_coverage = function_body(app_js, "renderCoverage", "optionLine")
    if "convertedPower.textContent" not in render_scores:
        failures.append("renderScores: representative converted score not rendered")
    if "primary.value" not in render_scores:
        failures.append("renderScores: representative score does not use primaryMetric.value")
    if "summary.hexaConverted380" not in render_scores:
        failures.append("renderScores: HEXA source fallback/detail missing")
    if "metricConfidence.textContent" not in render_scores:
        failures.append("renderScores: confidence card not populated")
    if "goal.label" not in render_scores:
        failures.append("renderScores: goal contract label is not shown with metric detail")
    if "goal.canCompareUsers" not in render_coverage or "goal.canRecommendItems" not in render_coverage:
        failures.append("renderCoverage: goal contract comparison/recommendation flags are not rendered")
    if "goal.metricValue" not in render_coverage:
        failures.append("renderCoverage: goal contract metric value is not rendered")

    if failures:
        raise AssertionError("\n".join(failures))


def main() -> None:
    assert_frontend_single_metric()
    print("OK: frontend renders one representative metric and confidence detail")


if __name__ == "__main__":
    main()
