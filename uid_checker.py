
# uid_checker.py
import httpx
import asyncio
import logging

logger = logging.getLogger("ff-uid-checker")

FF_API_URL  = "https://ff-info-nxt.vercel.app/api/player-info"
FF_API_PASS = "ic__Bjcs9tAvcs10tl_fdySzAo7"

REGION_MAP = {
    "bd": "bd", "ind": "ind", "sg": "sg", "id": "id",
    "th": "th", "my": "my",  "ph": "ph", "pk": "pk",
    "br": "br", "vn": "vn",  "tw": "tw", "na": "na",
}


async def check_uid(uid: str, region: str = "bd") -> dict:
    uid    = uid.strip()
    region = region.strip().lower()

    if not uid.isdigit():
        return {"success": False, "uid": uid, "region": region.upper(),
                "message": "Invalid UID ❌"}
    if not (5 <= len(uid) <= 15):
        return {"success": False, "uid": uid, "region": region.upper(),
                "message": "UID length invalid ❌"}

    params = {"uid": uid, "region": REGION_MAP.get(region, region), "pass": FF_API_PASS}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(FF_API_URL, params=params)
        data = resp.json()

        if resp.status_code != 200 or data.get("status") == "error":
            detail = data.get("error", {}).get("detail", "")
            msg    = data.get("error", {}).get("message", "Unknown error")
            return {"success": False, "uid": uid, "region": region.upper(),
                    "message": f"{detail or msg} ❌"}

        return _parse(uid, region, data)

    except httpx.TimeoutException:
        return {"success": False, "uid": uid, "region": region.upper(),
                "message": "API timeout ⏱️"}
    except Exception as e:
        return {"success": False, "uid": uid, "region": region.upper(),
                "message": f"Error: {str(e)} ❌"}


def _parse(uid: str, region: str, data: dict) -> dict:
    d       = data.get("data", {})
    basic   = d.get("basicInfo",       {})
    social  = d.get("socialInfo",      {})
    clan    = d.get("clanBasicInfo",   {})
    pet     = d.get("petInfo",         {})
    credit  = d.get("creditScoreInfo", {})
    diamond = d.get("diamondCostRes",  {})
    cdn     = d.get("cdnUrls",         {})
    profile = d.get("profileInfo",     {})

    gender   = (social.get("gender",   "") or "").replace("Gender_",   "").capitalize() or None
    language = (social.get("language", "") or "").replace("Language_", "").upper()      or None

    return {
        "success": True, "uid": uid, "region": basic.get("region", region.upper()),
        "nickname": basic.get("nickname"), "level": basic.get("level"),
        "exp": basic.get("exp"), "likes": basic.get("liked"),
        "badge_id": basic.get("badgeId"), "badge_count": basic.get("badgeCnt"),
        "title_id": basic.get("title"), "release_version": basic.get("releaseVersion"),
        "created_at": basic.get("createAt"), "last_login_at": basic.get("lastLoginAt"),
        "season_id": basic.get("seasonId"),
        "br_rank": basic.get("rank"), "br_rank_max": basic.get("maxRank"),
        "br_rank_points": basic.get("rankingPoints"),
        "cs_rank": basic.get("csRank"), "cs_rank_max": basic.get("csMaxRank"),
        "cs_rank_points": basic.get("csRankingPoints"),
        "gender": gender, "language": language, "bio": social.get("signature"),
        "credit_score": credit.get("creditScore"), "diamond_cost": diamond.get("diamondCost"),
        "guild": {"guild_id": str(clan.get("clanId","")), "guild_name": clan.get("clanName"),
                  "guild_level": clan.get("clanLevel"), "guild_members": clan.get("memberNum")
                  } if clan.get("clanId") else None,
        "pet": {"pet_id": pet.get("id"), "pet_level": pet.get("level"),
                "pet_exp": pet.get("exp"), "pet_skin_id": pet.get("skinId")
                } if pet else None,
        "avatar_url": cdn.get("avatar"), "banner_url": cdn.get("banner"),
        "avatar_id": cdn.get("avatarId"), "banner_id": cdn.get("bannerId"),
        "equipped_urls": cdn.get("equipped", []),
        "weapon_skin_urls": cdn.get("weaponSkins", []),
        "clothes": profile.get("clothes", []),
        "message": "Player found ✅",
    }


async def check_uids_batch(uids: list[str], region: str = "bd") -> list[dict]:
    return list(await asyncio.gather(*[check_uid(uid, region) for uid in uids]))
