from __future__ import annotations

import html
import re
import sys
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.calc import KMS_JOB_NAMES  # noqa: E402


OFFICIAL_JOB_GUIDE_URL = "https://maplestory.nexon.com/Guide/N23Job"


def normalize_job_name(value: str) -> str:
    return re.sub(r"\s+", "", value.strip())


def fetch_official_job_names() -> list[str]:
    request = Request(
        OFFICIAL_JOB_GUIDE_URL,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with urlopen(request, timeout=20) as response:
        page = response.read().decode("utf-8", "replace")

    names = []
    for raw_name in re.findall(r"char_info/char\d+\.png.*?<em>(.*?)</em>", page, re.S):
        name = html.unescape(re.sub(r"<.*?>", "", raw_name)).strip()
        if name and name not in names:
            names.append(name)
    return names


def assert_official_job_catalog() -> None:
    official_jobs = fetch_official_job_names()
    local_by_normalized = {normalize_job_name(job): job for job in KMS_JOB_NAMES}
    official_by_normalized = {normalize_job_name(job): job for job in official_jobs}

    failures: list[str] = []
    if len(official_jobs) < 48:
        failures.append(f"official guide returned too few jobs: {len(official_jobs)}")
    if len(KMS_JOB_NAMES) != len(official_jobs):
        failures.append(
            f"local job count {len(KMS_JOB_NAMES)} != official job count {len(official_jobs)}"
        )

    missing = sorted(set(official_by_normalized) - set(local_by_normalized))
    extra = sorted(set(local_by_normalized) - set(official_by_normalized))
    if missing:
        failures.append(
            "jobs missing from local formulas: "
            + ", ".join(official_by_normalized[key] for key in missing)
        )
    if extra:
        failures.append(
            "local formula jobs not found in official guide: "
            + ", ".join(local_by_normalized[key] for key in extra)
        )
    if normalize_job_name("레테") not in official_by_normalized:
        failures.append("official guide does not include 레테")
    if normalize_job_name("레테") not in local_by_normalized:
        failures.append("local formulas do not include 레테")

    if failures:
        raise AssertionError("\n".join(failures))


def main() -> None:
    assert_official_job_catalog()
    print(f"OK: local formulas match official Nexon guide jobs ({len(KMS_JOB_NAMES)} jobs)")


if __name__ == "__main__":
    main()
