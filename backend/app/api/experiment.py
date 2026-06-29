import json
import os
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/experiment", tags=["experiment"])


@router.get("/results")
async def get_experiment_results():
    results_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "scripts", "results.json")
    if not os.path.exists(results_path):
        raise HTTPException(status_code=404, detail="No experiment results found")
    with open(results_path, "r", encoding="utf-8") as f:
        return json.load(f)