from fastapi import APIRouter, HTTPException
import json, os

router = APIRouter(prefix="/api/experiment", tags=["experiment"])

RESULTS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "scripts", "experiment", "results.json")


@router.get("/results")
async def get_experiment_results():
    if not os.path.exists(RESULTS_PATH):
        raise HTTPException(status_code=404, detail="No experiment results found. Run the experiment framework first.")
    with open(RESULTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
