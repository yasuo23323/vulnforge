import os
fn = "D:\\大论文\\backend\\app\\api\\settings.py"
with open(fn, "r") as f:
    c = f.read()

extra = '''
@router.post("/test")
async def test_llm_connection():
    """Test the LLM API connection with a simple prompt."""
    api_key = app_settings.OPENAI_API_KEY
    if not api_key:
        return {"success": False, "message": "No LLM API key configured in .env"}
    import httpx
    base_url = (app_settings.OPENAI_BASE_URL or "https://api.openai.com").rstrip("/")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{base_url}/chat/completions",
                json={"model": app_settings.LLM_DEFAULT_MODEL, "messages": [{"role": "user", "content": "Reply OK in one word"}], "max_tokens": 10},
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                reply = data["choices"][0]["message"]["content"]
                return {"success": True, "model": app_settings.LLM_DEFAULT_MODEL, "reply": reply}
            else:
                return {"success": False, "message": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except Exception as e:
        return {"success": False, "message": str(e)}
'''

if "def test_llm_connection" not in c:
    with open(fn, "w") as f:
        f.write(c + extra)
    print("Test endpoint added")
else:
    print("Already exists")