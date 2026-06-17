from fastapi import APIRouter, HTTPException
from app.config import settings as app_settings

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
async def get_settings():
    return {
        "llm_provider": app_settings.LLM_DEFAULT_PROVIDER,
        "llm_model": app_settings.LLM_DEFAULT_MODEL,
        "database_type": app_settings.DATABASE_TYPE,
        "openai_key_set": bool(app_settings.OPENAI_API_KEY),
        "anthropic_key_set": bool(app_settings.ANTHROPIC_API_KEY),
    }


@router.post("/test")
async def test_llm_connection():
    """Test the LLM API connection with a simple prompt.
    Supports both OpenAI-compatible (DeepSeek etc.) and Anthropic providers.
    """
    import httpx

    provider = app_settings.LLM_DEFAULT_PROVIDER

    if provider == "anthropic":
        api_key = app_settings.ANTHROPIC_API_KEY
        if not api_key:
            return {"success": False, "message": "Anthropic API key not configured in .env"}
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    json={
                        "model": app_settings.LLM_DEFAULT_MODEL,
                        "messages": [{"role": "user", "content": "Reply OK in one word"}],
                        "max_tokens": 10,
                    },
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    timeout=15,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    reply = "".join(
                        block.get("text", "") for block in data.get("content", [])
                        if isinstance(block, dict) and block.get("type") == "text"
                    )
                    return {"success": True, "model": app_settings.LLM_DEFAULT_MODEL, "reply": reply}
                return {"success": False, "message": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    # Default: OpenAI-compatible (including DeepSeek, vLLM, etc.)
    api_key = app_settings.OPENAI_API_KEY
    if not api_key:
        return {"success": False, "message": "OpenAI/DeepSeek API key not configured in .env"}
    base_url = (app_settings.OPENAI_BASE_URL or "https://api.openai.com").rstrip("/")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{base_url}/chat/completions",
                json={
                    "model": app_settings.LLM_DEFAULT_MODEL,
                    "messages": [{"role": "user", "content": "Reply OK in one word"}],
                    "max_tokens": 10,
                },
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                reply = data["choices"][0]["message"]["content"]
                return {"success": True, "model": app_settings.LLM_DEFAULT_MODEL, "reply": reply}
            return {"success": False, "message": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except Exception as e:
        return {"success": False, "message": str(e)}
