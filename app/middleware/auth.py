import json
import os
from datetime import datetime, timezone
from fastapi import Request, HTTPException
from app.config import API_KEYS, TIER_LIMITS

USAGE_FILE = "usage_data.json"


def _load_usage() -> dict:
    if os.path.exists(USAGE_FILE):
        with open(USAGE_FILE, "r") as f:
            return json.load(f)
    return {}


def _save_usage(data: dict):
    with open(USAGE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _get_month_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _get_month_end() -> str:
    now = datetime.now(timezone.utc)
    if now.month == 12:
        next_month = now.replace(year=now.year + 1, month=1, day=1)
    else:
        next_month = now.replace(month=now.month + 1, day=1)
    return next_month.isoformat()


def get_api_key(request: Request) -> str:
    api_key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key. Include X-API-Key header.")
    if api_key not in API_KEYS:
        raise HTTPException(status_code=403, detail="Invalid API key.")
    return api_key


def check_rate_limit(api_key: str) -> dict:
    tier = API_KEYS.get(api_key, "free")
    limit = TIER_LIMITS.get(tier, 50)
    month_key = _get_month_key()

    usage = _load_usage()
    key_usage = usage.get(api_key, {})
    current_month_usage = key_usage.get(month_key, 0)

    if current_month_usage >= limit:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "tier": tier,
                "limit": limit,
                "used": current_month_usage,
                "resets_at": _get_month_end(),
                "upgrade": "Contact us to upgrade your plan.",
            },
        )

    if api_key not in usage:
        usage[api_key] = {}
    usage[api_key][month_key] = current_month_usage + 1
    _save_usage(usage)

    return {
        "tier": tier,
        "requests_used": current_month_usage + 1,
        "requests_limit": limit,
        "resets_at": _get_month_end(),
    }


def get_usage_without_increment(api_key: str) -> dict:
    tier = API_KEYS.get(api_key, "free")
    limit = TIER_LIMITS.get(tier, 50)
    month_key = _get_month_key()

    usage = _load_usage()
    key_usage = usage.get(api_key, {})
    current_month_usage = key_usage.get(month_key, 0)

    return {
        "tier": tier,
        "requests_used": current_month_usage,
        "requests_limit": limit,
        "resets_at": _get_month_end(),
    }
