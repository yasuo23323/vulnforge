from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional
import asyncio

from app.database import get_db
from app.models import ScanTask, ScanStatus
from app.schemas.scan import ScanCreate, ScanUpdate, ScanResponse, ScanListResponse
from app.scanner.runner import run_scan_task

router = APIRouter(prefix="/api/scans", tags=["scans"])


@router.post("", response_model=ScanResponse)
async def create_scan(scan_data: ScanCreate, db: AsyncSession = Depends(get_db)):
    scan = ScanTask(
        target_url=scan_data.target_url,
        target_name=scan_data.target_name or scan_data.target_url,
        scanners=scan_data.scanners,
        parameters=scan_data.parameters,
        status=ScanStatus.PENDING.value,
    )
    db.add(scan)
    await db.commit()
    await db.refresh(scan)

    # Run scan asynchronously
    asyncio.create_task(run_scan_task(scan.id))

    return scan


@router.get("", response_model=ScanListResponse)
async def list_scans(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    total_q = select(func.count(ScanTask.id))
    total = (await db.execute(total_q)).scalar() or 0

    q = select(ScanTask).order_by(desc(ScanTask.created_at)).offset((page - 1) * page_size).limit(page_size)
    scans = (await db.execute(q)).scalars().all()

    items = []
    for s in scans:
        d = {
            "id": s.id,
            "target_url": s.target_url,
            "target_name": s.target_name,
            "scanners": s.scanners,
            "parameters": s.parameters,
            "status": s.status,
            "error_message": s.error_message,
            "created_at": s.created_at,
            "started_at": s.started_at,
            "completed_at": s.completed_at,
            "updated_at": s.updated_at,
            "findings_count": len(s.findings) if s.findings else 0,
        }
        items.append(d)

    return ScanListResponse(items=items, total=total)


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(scan_id: str, db: AsyncSession = Depends(get_db)):
    scan = await db.get(ScanTask, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@router.delete("/{scan_id}")
async def delete_scan(scan_id: str, db: AsyncSession = Depends(get_db)):
    scan = await db.get(ScanTask, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    await db.delete(scan)
    await db.commit()
    return {"ok": True}