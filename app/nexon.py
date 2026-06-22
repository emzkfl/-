from __future__ import annotations

import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from calc import build_view_model


BASE_URL = "https://open.api.nexon.com/maplestory/v1"
ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
CACHE_TTL_SECONDS = 300
REQUEST_GAP_SECONDS = 0.12
TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 504}
TRANSIENT_MESSAGES = ("please try again later",)
_CACHE: dict[tuple[str, str], tuple[float, dict[str, Any]]] = {}
_CACHE_LOCK = Lock()


class NexonApiError(RuntimeError):
    pass


def load_env() -> None:
    if not ENV_PATH.exists():
        return
    for raw_line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def api_key() -> str:
    load_env()
    for name in ("NEXON_API_KEY", "NEXON_OPEN_API_KEY", "NXOPEN_API_KEY", "API_KEY"):
        value = os.environ.get(name)
        if value:
            return value
    raise NexonApiError(".env에 NEXON_API_KEY가 없습니다.")


def default_date() -> str:
    kst = timezone(timedelta(hours=9))
    return (datetime.now(kst) - timedelta(days=1)).strftime("%Y-%m-%d")


def normalize_character_name(character_name: str) -> str:
    name = "".join(str(character_name or "").replace("\u3000", " ").split())
    if not name:
        raise NexonApiError("닉네임을 입력해주세요.")
    return name


def normalize_lookup_date(date: str | None = None) -> str:
    text = str(date or "").strip() or default_date()
    try:
        parsed = datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError as exc:
        raise NexonApiError("조회일은 YYYY-MM-DD 형식으로 입력해주세요.") from exc

    max_text = default_date()
    max_date = datetime.strptime(max_text, "%Y-%m-%d").date()
    if parsed > max_date:
        raise NexonApiError(f"조회일은 오늘 이전 날짜만 가능합니다. {max_text} 이하로 선택해주세요.")
    return parsed.isoformat()


def is_transient_error(status: int | None, message: str) -> bool:
    normalized = message.lower()
    return status in TRANSIENT_STATUS_CODES or any(
        marker in normalized for marker in TRANSIENT_MESSAGES
    )


def explain_api_error(message: str) -> str:
    if "please input valid parameter" in message.lower():
        return (
            "요청 파라미터가 유효하지 않습니다. 닉네임과 조회일을 확인해주세요. "
            "조회일은 오늘 이전 날짜만 가능합니다."
        )
    if "please try again later" in message.lower():
        return (
            "Nexon API가 요청 제한 또는 혼잡 상태입니다. "
            "잠시 후 다시 조회해주세요. 계속 반복되면 API 키의 사용량 제한에 걸렸을 수 있습니다."
        )
    return message


def request_json(path: str, params: dict[str, Any], retries: int = 3) -> dict[str, Any]:
    query = urlencode({key: value for key, value in params.items() if value not in (None, "")})
    url = f"{BASE_URL}{path}"
    if query:
        url += f"?{query}"

    last_error: Exception | None = None
    for attempt in range(retries + 1):
        request = Request(url, headers={"x-nxopen-api-key": api_key()})
        try:
            with urlopen(request, timeout=12) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            status = getattr(exc, "code", None)
            try:
                body = json.loads(exc.read().decode("utf-8"))
                message = body.get("error", {}).get("message") or body.get("message") or str(body)
            except Exception:
                message = exc.reason
            last_error = NexonApiError(f"Nexon API 오류: {explain_api_error(str(message))}")
            retryable = is_transient_error(status, str(message))
        except URLError as exc:
            last_error = NexonApiError(f"Nexon API 연결 실패: {exc.reason}")
            retryable = True

        if attempt < retries and retryable:
            time.sleep(min(5.0, 0.9 * (2 ** attempt)))
        else:
            break

    raise last_error or NexonApiError("Nexon API 오류")


ENDPOINTS = {
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


REQUIRED = {"basic", "stat", "itemEquipment"}
SKILL_GRADES = ("5", "6")


def fetch_character(character_name: str, date: str | None = None) -> dict[str, Any]:
    name = normalize_character_name(character_name)
    target_date = normalize_lookup_date(date)
    cache_key = (name.casefold(), target_date)
    with _CACHE_LOCK:
        cached = _CACHE.get(cache_key)
        if cached and time.time() - cached[0] < CACHE_TTL_SECONDS:
            return cached[1]

    ocid_payload = request_json("/id", {"character_name": name})
    ocid = ocid_payload.get("ocid")
    if not ocid:
        raise NexonApiError("캐릭터 OCID를 찾지 못했습니다.")

    raw: dict[str, Any] = {"ocid": ocid, "date": target_date, "warnings": []}

    def fetch_one(key: str, path: str, params: dict[str, Any]) -> tuple[str, dict[str, Any] | None, str | None]:
        try:
            return key, request_json(path, params), None
        except Exception as exc:
            return key, None, str(exc)

    requests = [
        (key, path, {"ocid": ocid, "date": target_date})
        for key, path in ENDPOINTS.items()
    ]
    requests.extend(
        (
            f"skill{grade}",
            "/character/skill",
            {"ocid": ocid, "date": target_date, "character_skill_grade": grade},
        )
        for grade in SKILL_GRADES
    )

    for key, path, params in requests:
        key, payload, error = fetch_one(key, path, params)
        if error:
            if key in REQUIRED:
                raise NexonApiError(error)
            raw["warnings"].append({"section": key, "message": error})
        else:
            raw[key] = payload or {}
        time.sleep(REQUEST_GAP_SECONDS)

    result = build_view_model(raw)
    with _CACHE_LOCK:
        _CACHE[cache_key] = (time.time(), result)
    return result
