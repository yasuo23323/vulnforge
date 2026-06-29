from fastapi import APIRouter, HTTPException
from app.config import settings as app_settings
import httpx

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
async def get_settings():
    return {
        "database_type": app_settings.DATABASE_TYPE,
        "openai_key_set": bool(app_settings.OPENAI_API_KEY),
        "anthropic_key_set": bool(app_settings.ANTHROPIC_API_KEY),
        "llm_default_provider": app_settings.LLM_DEFAULT_PROVIDER,
        "llm_default_model": app_settings.LLM_DEFAULT_MODEL,
    }


@router.post("/test")
async def test_llm_connection():
    if app_settings.OPENAI_API_KEY:
        try:
            async with httpx.AsyncClient() as client:
                url = f"{app_settings.OPENAI_BASE_URL.rstrip('/')}/chat/completions"
                headers = {
                    "Authorization": f"Bearer {app_settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                }
                body = {
                    "model": app_settings.LLM_DEFAULT_MODEL,
                    "messages": [{"role": "user", "content": "Reply OK in one word"}],
                    "max_tokens": 10,
                }
                resp = await client.post(url, json=body, headers=headers, timeout=15)
                if resp.status_code == 200:
                    return {"status": "ok", "provider": "openai"}
                return {"status": "error", "detail": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    if app_settings.ANTHROPIC_API_KEY:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": app_settings.ANTHROPIC_API_KEY,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "claude-3-haiku-20240307",
                        "max_tokens": 10,
                        "messages": [{"role": "user", "content": "Reply OK in one word"}],
                    },
                    timeout=15,
                )
                if resp.status_code == 200:
                    return {"status": "ok", "provider": "anthropic"}
                return {"status": "error", "detail": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    raise HTTPException(status_code=400, detail="No LLM API key configured")