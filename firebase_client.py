
# firebase_client.py — Firebase Realtime DB via REST API
# ────────────────────────────────────────────────────────────
import httpx
import time
import secrets
import string
import logging
from urllib.parse import quote

logger = logging.getLogger("firebase")

FIREBASE_URL = "https://version-7c25f-default-rtdb.firebaseio.com"


def _safe_key(key: str) -> str:
    """
    Firebase Realtime DB path-এ `.`, `$`, `#`, `[`, `]`, `/` এবং `-`
    কিছু ক্ষেত্রে সমস্যা করে।
    Key-টাকে URL-encode করে safe path তৈরি করি।
    """
    return quote(key, safe="")


def _url(path: str) -> str:
    return f"{FIREBASE_URL}/{path}.json"


# ── Generate API Key ──────────────────────────────────────────────────────
def generate_api_key() -> str:
    """vx-XXXXXXXXXXXXXXXX format এ key বানাও"""
    chars = string.ascii_letters + string.digits
    random_part = ''.join(secrets.choice(chars) for _ in range(20))
    return f"vx-{random_part}"


# ── Read Key from Firebase ────────────────────────────────────────────────
async def get_api_key(key: str) -> dict | None:
    safe = _safe_key(key)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(_url(f"api_keys/{safe}"))
        if resp.status_code == 200 and resp.json():
            return resp.json()
        return None
    except Exception as e:
        logger.error(f"Firebase read error: {e}")
        return None


# ── Increment Request Count ───────────────────────────────────────────────
async def increment_usage(key: str, current_used: int):
    """
    requests_used কে +1 করে Firebase-এ update করো।
    Firebase Transaction না থাকায় optimistic increment ব্যবহার করছি।
    """
    safe = _safe_key(key)
    new_count = current_used + 1
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.patch(
                _url(f"api_keys/{safe}"),
                json={"requests_used": new_count}
            )
        if resp.status_code == 200:
            logger.info(f"✅ Request count updated: {key} → {new_count}")
        else:
            logger.warning(f"⚠️ Firebase patch failed [{resp.status_code}]: {resp.text}")
    except Exception as e:
        logger.error(f"Firebase update error: {e}")


# ── Validate API Key ──────────────────────────────────────────────────────
async def validate_api_key(key: str) -> dict:
    """
    Returns:
      {"valid": True, "data": {...}}
      {"valid": False, "error": "...", "code": "..."}
    """
    if not key or not key.startswith("vx-"):
        return {"valid": False, "error": "Invalid API key format ❌", "code": "INVALID_KEY"}

    data = await get_api_key(key)

    if not data:
        return {"valid": False, "error": "API key not found ❌", "code": "KEY_NOT_FOUND"}

    if not data.get("is_active", False):
        return {"valid": False, "error": "API key is disabled ❌", "code": "KEY_DISABLED"}

    # Expiry check
    expires_at = data.get("expires_at", 0)
    if expires_at and int(time.time()) > int(expires_at):
        return {"valid": False, "error": "API key expired ❌", "code": "KEY_EXPIRED"}

    # Request limit check
    limit = data.get("request_limit", 0)
    used  = data.get("requests_used", 0)
    if limit > 0 and used >= limit:
        return {
            "valid": False,
            "error": f"Request limit exceeded ({used}/{limit}) ❌",
            "code": "LIMIT_EXCEEDED"
        }

    # ✅ Valid — increment usage AFTER all checks pass
    await increment_usage(key, used)

    return {
        "valid": True,
        "data": data,
        "requests_used": used + 1,
        "request_limit": limit,
    }
