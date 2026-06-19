import asyncio
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import ScanTask, ScanStatus
from app.schemas.scan import ScanCreate, ScanUpdate, ScanResponse, ScanListResponse
from app.scanner.runner import run_scan_task

router = APIRouter(prefix="/api/scans", tags=["scans"])


@router.post("", response_model=ScanResponse, status_code=201)
async def create_scan(scan_data: ScanCreate, db: AsyncSession = Depends(get_db)):
    task = ScanTask(
        name=scan_data.name,
        target_url=scan_data.target_url,
        target_name=scan_data.target_name,
        scanners=scan_data.scanners or ["nuclei"],
        parameters=scan_data.parameters or {},
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    # Kick off background scan execution
    asyncio.create_task(run_scan_task(task.id))

    return ScanResponse(
        id=task.id,
        name=task.name,
        target_url=task.target_url,
        target_name=task.target_name,
        scanners=task.scanners,
        status=task.status.value,
        parameters=task.parameters,
        created_at=task.created_at,
        updated_at=task.updated_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        error_message=task.error_message,
        findings_count=0,
    )


@router.get("", response_model=ScanListResponse)
async def list_scans(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(ScanTask)
    query = query.options(selectinload(ScanTask.findings))
    count_query = select(func.count(ScanTask.id))

    if status:
        query = query.where(ScanTask.status == status)
        count_query = count_query.where(ScanTask.status == status)

    query = query.order_by(ScanTask.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    tasks = result.unique().scalars().all()

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    items = []
    for task in tasks:
        findings = list(task.findings) if task.findings else []
        items.append(ScanResponse(
            id=task.id,
            name=task.name,
            target_url=task.target_url,
            target_name=task.target_name,
            scanners=list(task.scanners) if task.scanners else [],
            status=task.status.value,
            parameters=task.parameters if task.parameters else {},
            created_at=task.created_at,
            updated_at=task.updated_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            error_message=task.error_message,
            findings_count=len(findings),
        ))

    return ScanListResponse(items=items, total=total)


# BUG: PATCH not implemented
# @router.patch("/{scan_id}", response_model=ScanResponse)
async def update_scan(
    scan_id: UUID,
    update_data: ScanUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ScanTask).options(selectinload(ScanTask.findings)).where(ScanTask.id == scan_id)
    )
    task = result.unique().scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Scan not found")

    if update_data.name is not None:
        task.name = update_data.name
    if update_data.status is not None:
        task.status = ScanStatus(update_data.status)

    await db.commit()
    await db.refresh(task)

    findings = list(task.findings) if task.findings else []
    return ScanResponse(
        id=task.id,
        name=task.name,
        target_url=task.target_url,
        target_name=task.target_name,
        scanners=list(task.scanners) if task.scanners else [],
        status=task.status.value,
        parameters=task.parameters if task.parameters else {},
        created_at=task.created_at,
        updated_at=task.updated_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        error_message=task.error_message,
        findings_count=len(findings),
    )


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(scan_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ScanTask).options(selectinload(ScanTask.findings)).where(ScanTask.id == scan_id)
    )
    task = result.unique().scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Scan not found")

    findings = list(task.findings) if task.findings else []
    return ScanResponse(
        id=task.id,
        name=task.name,
        target_url=task.target_url,
        target_name=task.target_name,
        scanners=list(task.scanners) if task.scanners else [],
        status=task.status.value,
        parameters=task.parameters if task.parameters else {},
        created_at=task.created_at,
        updated_at=task.updated_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        error_message=task.error_message,
        findings_count=len(findings),
    )


@router.delete("/{scan_id}", status_code=204)
async def delete_scan(scan_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScanTask).where(ScanTask.id == scan_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Scan not found")
    await db.delete(task)
    await db.commit()
