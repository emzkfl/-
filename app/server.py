from __future__ import annotations

import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from calc import BOSS_RULES, BOSS_FORCE_SOURCE, calculation_coverage, job_formula_manifest
from nexon import NexonApiError, default_date, fetch_character


STATIC_DIR = Path(__file__).resolve().parent / "static"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def log_message(self, format, *args):  # noqa: A002
        return

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("Pragma", "no-cache")
        super().end_headers()

    def send_json(self, status: int, payload: dict | list) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/health":
            self.send_json(200, {"ok": True, "defaultDate": default_date()})
            return
        if path == "/api/formulas":
            manifest = job_formula_manifest()
            coverage = calculation_coverage("레테")
            self.send_json(
                200,
                {
                    "ok": True,
                    "metricId": "unifiedConverted380",
                    "metricLabel": "대표 환산(380)",
                    "formulaSource": manifest["source"],
                    "jobCount": manifest["jobCount"],
                    "knownJobs": manifest["knownJobs"],
                    "jobs": manifest["jobs"],
                    "bossRuleCount": len(BOSS_RULES),
                    "bossRules": BOSS_RULES,
                    "coverage": {
                        "targetJobs": coverage["targetJobs"],
                        "coveredDetailJobs": coverage["coveredDetailJobs"],
                        "coveredMultiplierJobs": coverage["coveredMultiplierJobs"],
                        "coveredCombatJobs": coverage["coveredCombatJobs"],
                        "missingDetailJobs": coverage["missingDetailJobs"],
                        "missingMultiplierJobs": coverage["missingMultiplierJobs"],
                        "missingCombatJobs": coverage["missingCombatJobs"],
                    },
                    "formulas": {
                        "mainStat": "기본스탯 * (1 + 스탯% / 100) + % 미적용",
                        "attack": "공격력/마력 * (1 + 공격력%/마력% / 100)",
                        "damageFactor": "(1 + (보공 + 데미지) / 100) * (1 + 최종뎀 / 100) * 방어율계수 * 크리계수 * 주스탯계수 * 공격력계수 * 속성계수 * 무기상수 * 0.01 * 숙련도평균",
                        "representativeMetric": "round(HEXA 보정 환산 380)",
                        "bossEffectiveMetric": "대표 환산 * sqrt(방어율보정 * 포스보정 * 보스별 심볼 보너스)",
                        "bossRatio": "보스별 유효 환산 / 요구 환산 * 100",
                    },
                    "bossForceSource": BOSS_FORCE_SOURCE,
                },
            )
            return
        if path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self):  # noqa: N802
        path = urlparse(self.path).path
        if path != "/api/character":
            self.send_json(404, {"error": "not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 1024 * 1024:
                raise ValueError("요청이 너무 큽니다.")
            body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            if not isinstance(body, dict):
                raise ValueError("JSON 객체를 보내주세요.")

            self.send_json(
                200,
                fetch_character(
                    str(body.get("characterName") or ""),
                    str(body.get("date") or "") or None,
                ),
            )
        except (NexonApiError, ValueError, json.JSONDecodeError) as exc:
            self.send_json(400, {"error": str(exc)})
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self.send_json(500, {"error": f"서버 오류: {exc}"})


def main() -> None:
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "4176"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Serving on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
