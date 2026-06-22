from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


INDEX = ROOT / "app" / "static" / "index.html"
APP_JS = ROOT / "app" / "static" / "app.js"


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

    render_scores_start = app_js.find("function renderScores")
    render_scores_end = app_js.find("function presetByNo", render_scores_start)
    render_scores = app_js[render_scores_start:render_scores_end]
    if "convertedPower.textContent" not in render_scores:
        failures.append("renderScores: representative converted score not rendered")
    if "primary.value" not in render_scores:
        failures.append("renderScores: representative score does not use primaryMetric.value")
    if "summary.hexaConverted380" not in render_scores:
        failures.append("renderScores: HEXA source fallback/detail missing")
    if "metricConfidence.textContent" not in render_scores:
        failures.append("renderScores: confidence card not populated")

    if failures:
        raise AssertionError("\n".join(failures))


def main() -> None:
    assert_frontend_single_metric()
    print("OK: frontend renders one representative metric and confidence detail")


if __name__ == "__main__":
    main()
