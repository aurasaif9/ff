
# main.py — Paid API with Firebase API key validation
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from uid_checker import check_uid, check_uids_batch
from firebase_client import validate_api_key

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="🔫 Free Fire UID Checker — Paid API",
    description="""
## Free Fire Player Info API (Paid)

**API Key required!** Admin panel থেকে key নাও।

### Usage
```
GET /check?uid=3238846823&region=bd&Api_key=vx-YOUR_KEY
```

### Error Codes
| Code | Meaning |
|------|---------|
| `INVALID_KEY` | API key format ভুল |
| `KEY_NOT_FOUND` | Key exist করে না |
| `KEY_DISABLED` | Admin disable করেছে |
| `KEY_EXPIRED` | Expiry শেষ |
| `LIMIT_EXCEEDED` | Request limit শেষ |
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── API Key Error Response ────────────────────────────────────
def key_error(code: str, message: str, status: int = 403):
    return JSONResponse(
        status_code=status,
        content={
            "success": False,
            "error": {"code": code, "message": message}
        }
    )


# ══════════════════════════════════════════════════════════════
#  ENDPOINTS
# ══════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    return {
        "name": "Free Fire UID Checker API",
        "version": "2.0.0",
        "docs": "/docs",
        "status": "running ✅",
        "note": "API key required. Contact admin for key."
    }


@app.get("/regions")
async def regions():
    return {
        "regions": {
            "bd": "Bangladesh 🇧🇩", "ind": "India 🇮🇳",
            "sg": "Singapore 🇸🇬",  "id":  "Indonesia 🇮🇩",
            "th": "Thailand 🇹🇭",   "my":  "Malaysia 🇲🇾",
            "ph": "Philippines 🇵🇭","pk":  "Pakistan 🇵🇰",
            "br": "Brazil 🇧🇷",     "vn":  "Vietnam 🇻🇳",
            "tw": "Taiwan 🇹🇼",
        }
    }


# ── GET /check ────────────────────────────────────────────────
@app.get("/check", summary="Single UID Check (Paid)")
async def check_get(
    uid:     str = Query(..., example="3238846823"),
    region:  str = Query(default="bd", example="bd"),
    Api_key: str = Query(..., description="Your API key (from admin panel)", example="vx-XXXX"),
):
    """
    **Usage:** `/check?uid=3238846823&region=bd&Api_key=vx-YOUR_KEY`
    """
    # ── Validate API Key ──────────────────────────────────────
    validation = await validate_api_key(Api_key)
    if not validation["valid"]:
        return key_error(
            code    = validation.get("code", "INVALID_KEY"),
            message = validation.get("error", "Invalid API key")
        )

    # ── Process Request ───────────────────────────────────────
    result = await check_uid(uid, region)
    return result


# ── POST /check ───────────────────────────────────────────────
@app.post("/check", summary="Single UID Check POST (Paid)")
async def check_post(
    body:    dict,
    Api_key: str = Query(...),
):
    validation = await validate_api_key(Api_key)
    if not validation["valid"]:
        return key_error(validation.get("code", "INVALID_KEY"), validation.get("error", ""))

    uid    = body.get("uid", "")
    region = body.get("region", "bd")
    return await check_uid(uid, region)


# ── POST /check/batch ─────────────────────────────────────────
@app.post("/check/batch", summary="Batch UID Check (Paid)")
async def check_batch(
    body:    dict,
    Api_key: str = Query(...),
):
    validation = await validate_api_key(Api_key)
    if not validation["valid"]:
        return key_error(validation.get("code", "INVALID_KEY"), validation.get("error", ""))

    uids   = body.get("uids", [])
    region = body.get("region", "bd")

    if not uids or len(uids) > 10:
        raise HTTPException(status_code=400, detail="1-10 UIDs required ❌")

    results = await check_uids_batch(uids, region)
    return {"success": True, "total": len(results), "results": results}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
