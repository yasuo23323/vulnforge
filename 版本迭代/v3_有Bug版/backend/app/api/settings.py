from fastapi import APIRouter
from app.config import settings

router = APIRouter(prefix="/api/settings", tags=["settings"])

@router.get("") async def get():
    return {"llm_provider": settings.LLM_DEFAULT_PROVIDER, "llm_model": settings.LLM_DEFAULT_MODEL}

# BUG: only OpenAI, no Anthropic support
@router.post("/test") async def test():
    import httpx
    if not settings.OPENAI_API_KEY: return {"success": False, "message": "No key"}
    r = await httpx.AsyncClient().post("https://api.openai.com/v1/chat/completions",
        json={"model": settings.LLM_DEFAULT_MODEL, "messages":[{"role":"user","content":"OK"}]},
        headers={"Authorization": "Bearer " + settings.OPENAI_API_KEY})
    return {"success": r.status_code == 200}
