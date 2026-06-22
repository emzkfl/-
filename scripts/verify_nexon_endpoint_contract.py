from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "app"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(APP_DIR))

from app.calc import API_OPTIONAL_SECTIONS, API_REQUIRED_SECTIONS  # noqa: E402
import nexon  # noqa: E402


EXPECTED_ENDPOINT_PATHS = {
    "basic": "/character/basic",
    "stat": "/character/stat",
    "itemEquipment": "/character/item-equipment",
    "symbol": "/character/symbol-equipment",
    "ability": "/character/ability",
    "setEffect": "/character/set-effect",
    "hyperStat": "/character/hyper-stat",
    "otherStat": "/character/other-stat",
    "hexamatrixStat": "/character/hexamatrix-stat",
    "union": "/user/union",
    "petEquipment": "/character/pet-equipment",
    "linkSkill": "/character/link-skill",
    "vmatrix": "/character/vmatrix",
    "hexamatrix": "/character/hexamatrix",
    "ringExchangeSkillEquipment": "/character/ring-exchange-skill-equipment",
    "ringReserveSkillEquipment": "/character/ring-reserve-skill-equipment",
}

PROHIBITED_ENDPOINT_KEYS = {
    "popularity",
    "dojang",
}


def assert_nexon_endpoint_contract() -> None:
    expected_sections = set(API_REQUIRED_SECTIONS) | set(API_OPTIONAL_SECTIONS)
    fetched_sections = set(nexon.ENDPOINTS) | {f"skill{grade}" for grade in nexon.SKILL_GRADES}
    failures: list[str] = []

    if set(nexon.REQUIRED) != set(API_REQUIRED_SECTIONS):
        failures.append(f"required endpoint set {sorted(nexon.REQUIRED)} != {sorted(API_REQUIRED_SECTIONS)}")

    missing = sorted(expected_sections - fetched_sections)
    extra = sorted(fetched_sections - expected_sections)
    if missing:
        failures.append(f"calculation input sections not fetched from Nexon API: {missing}")
    if extra:
        failures.append(f"fetched Nexon API sections not consumed by calculation audit: {extra}")

    for key, path in EXPECTED_ENDPOINT_PATHS.items():
        if nexon.ENDPOINTS.get(key) != path:
            failures.append(f"endpoint {key} path {nexon.ENDPOINTS.get(key)!r} != {path!r}")

    prohibited = sorted(PROHIBITED_ENDPOINT_KEYS & set(nexon.ENDPOINTS))
    if prohibited:
        failures.append(f"quota-wasting endpoints should not be fetched: {prohibited}")

    skill_sections = {f"skill{grade}" for grade in nexon.SKILL_GRADES}
    if skill_sections != {"skill5", "skill6"}:
        failures.append(f"skill grade sections changed: {sorted(skill_sections)}")

    if failures:
        raise AssertionError("\n".join(failures))


def main() -> None:
    assert_nexon_endpoint_contract()
    print("OK: Nexon endpoint contract matches calculation input contract")


if __name__ == "__main__":
    main()
