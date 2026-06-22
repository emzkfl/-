from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PYTHON_COMPILE_TARGETS = [
    "app/calc.py",
    "app/server.py",
    "app/nexon.py",
    "scripts/verify_all.py",
    "scripts/verify_calculation.py",
    "scripts/verify_calibration_tables.py",
    "scripts/verify_goal_readiness.py",
    "scripts/verify_official_job_catalog.py",
    "scripts/verify_nexon_endpoint_contract.py",
    "scripts/verify_fetch_character_contract.py",
    "scripts/verify_server_http_contract.py",
    "scripts/verify_frontend_single_metric.py",
    "scripts/verify_frontend_repair_output.py",
    "scripts/verify_ranking_single_metric.py",
]

VERIFY_SCRIPTS = [
    "scripts/verify_calculation.py",
    "scripts/verify_calibration_tables.py",
    "scripts/verify_goal_readiness.py",
    "scripts/verify_official_job_catalog.py",
    "scripts/verify_nexon_endpoint_contract.py",
    "scripts/verify_fetch_character_contract.py",
    "scripts/verify_server_http_contract.py",
    "scripts/verify_frontend_single_metric.py",
    "scripts/verify_frontend_repair_output.py",
    "scripts/verify_ranking_single_metric.py",
]


def run_step(label: str, command: list[str]) -> None:
    printable = " ".join(command)
    print(f"\n== {label} ==", flush=True)
    print(printable, flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> None:
    run_step(
        "Python syntax",
        [sys.executable, "-m", "py_compile", *PYTHON_COMPILE_TARGETS],
    )
    run_step("JavaScript syntax", ["node", "--check", "app/static/app.js"])
    for script in VERIFY_SCRIPTS:
        run_step(script, [sys.executable, script])
    print("\nOK: all verification gates passed", flush=True)


if __name__ == "__main__":
    main()
