import logging
from datetime import datetime, timezone

from fastapi import Request, HTTPException
from redis.asyncio import Redis

from app.config import API_KEYS, TIER_LIMITS, REDIS_URL, RAPIDAPI_PROXY_SECRET

logger = logging.getLogger(__name__)

_redis: Redis | None = None


async def init_redis():
    global _redis
    try:
        _redis = Redis.from_url(REDIS_URL, decode_responses=True)
        await _redis.ping()
        logger.info("Redis connected")
    except Exception:
        logger.error("Failed to connect to Redis, rate limiting will be disabled")
        _redis = None


async def close_redis():
    global _redis
    if _redis:
        await _redis.close()
        logger.info("Redis connection closed")


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
    # RapidAPI proxy check
    if RAPIDAPI_PROXY_SECRET:
        proxy_secret = request.headers.get("X-RapidAPI-Proxy-Secret")
        if proxy_secret == RAPIDAPI_PROXY_SECRET:
            user = request.headers.get("X-RapidAPI-User", "rapidapi-user")
            logger.info(f"RapidAPI request from user: {user}")
            return f"rapidapi:{user}"

    api_key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key. Include X-API-Key header.")
    if api_key not in API_KEYS:
        raise HTTPException(status_code=403, detail="Invalid API key.")
    return api_key


async def check_rate_limit(api_key: str) -> dict:
    tier = API_KEYS.get(api_key, "free")
    limit = TIER_LIMITS.get(tier, 50)
    month_key = _get_month_key()
    redis_key = f"usage:{api_key}:{month_key}"

    if not _redis:
        logger.warning("Redis unavailable, skipping rate limit check")
        return {
            "tier": tier,
            "requests_used": -1,
            "requests_limit": limit,
            "resets_at": _get_month_end(),
        }

    try:
        current = await _redis.get(redis_key)
        current_count = int(current) if current else 0

        if current_count >= limit:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "tier": tier,
                    "limit": limit,
                    "used": current_count,
                    "resets_at": _get_month_end(),
                    "upgrade": "Contact us to upgrade your plan.",
                },
            )

        new_count = await _redis.incr(redis_key)
        if new_count == 1:
            await _redis.expire(redis_key, 60 * 60 * 24 * 35)  # 35-day TTL

        return {
            "tier": tier,
            "requests_used": new_count,
            "requests_limit": limit,
            "resets_at": _get_month_end(),
        }
    except HTTPException:
        raise
    except Exception:
        logger.error("Redis error during rate limit check, allowing request")
        return {
            "tier": tier,
            "requests_used": -1,
            "requests_limit": limit,
            "resets_at": _get_month_end(),
        }


async def get_usage_without_increment(api_key: str) -> dict:
    tier = API_KEYS.get(api_key, "free")
    limit = TIER_LIMITS.get(tier, 50)
    month_key = _get_month_key()
    redis_key = f"usage:{api_key}:{month_key}"

    if not _redis:
        return {
            "tier": tier,
            "requests_used": -1,
            "requests_limit": limit,
            "resets_at": _get_month_end(),
        }

    try:
        current = await _redis.get(redis_key)
        current_count = int(current) if current else 0
    except Exception:
        logger.error("Redis error during usage check")
        current_count = -1

    return {
        "tier": tier,
        "requests_used": current_count,
        "requests_limit": limit,
        "resets_at": _get_month_end(),
    }
