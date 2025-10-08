import os
from fastapi import Header, HTTPException

def get_plan_from_key(api_key: str) -> str:
    free_keys = [k.strip() for k in os.getenv("API_KEYS_FREE", "").split(",") if k.strip()]
    pro_keys = [k.strip() for k in os.getenv("API_KEYS_PRO", "").split(",") if k.strip()]
    if api_key in pro_keys:
        return "pro"
    if api_key in free_keys:
        return "free"
    return ""

async def api_key_auth(x_api_key: str = Header(default="")) -> str:
    plan = get_plan_from_key(x_api_key)
    if not plan:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return plan
