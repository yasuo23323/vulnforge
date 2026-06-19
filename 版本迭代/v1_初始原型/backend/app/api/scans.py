from fastapi import APIRouter

router = APIRouter(prefix="/api/scans")

@router.post("") async def create(name: str, target: str):
    return {"status": "created", "name": name, "target": target}

@router.get("") async def list():
    return {"items": [], "total": 0}
