import os
import uuid
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.dependencies import get_current_client
from app.models.client import Client
from app.models.lab_result import LabResult
from app.schemas.health import LabOCRResult, LabResultCreate, LabResultResponse
from app.services.lab_ocr_service import extract_labs_from_pdf

router = APIRouter(prefix="/labs", tags=["health"])

UPLOAD_DIR = Path(settings.UPLOAD_DIR) / "labs"


@router.get("", response_model=list[LabResultResponse])
async def list_labs(
    marker_name: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    client: Client = Depends(get_current_client),
):
    """List lab results, optionally filtered by marker name."""
    query = select(LabResult).where(LabResult.client_id == client.id)
    if marker_name:
        query = query.where(LabResult.marker_name.ilike(f"%{marker_name}%"))
    query = query.order_by(LabResult.test_date.desc()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/upload", response_model=LabOCRResult)
async def upload_lab_pdf(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    client: Client = Depends(get_current_client),
):
    """
    Upload a lab report PDF. Returns extracted biomarkers for user confirmation.
    Call POST /labs/confirm to save after reviewing.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = f"{client.id}_{uuid.uuid4().hex}.pdf"
    file_path = UPLOAD_DIR / safe_name

    contents = await file.read()
    file_path.write_bytes(contents)

    try:
        ocr_result = await extract_labs_from_pdf(str(file_path))
    except Exception as e:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"Failed to extract lab data: {e}")

    # Attach the file path so the confirm endpoint can reference it
    ocr_result.__dict__["_pdf_path"] = str(file_path)
    return ocr_result


@router.post("/confirm", response_model=list[LabResultResponse], status_code=status.HTTP_201_CREATED)
async def confirm_lab_results(
    payload: LabOCRResult,
    source_pdf_url: str | None = None,
    db: AsyncSession = Depends(get_db),
    client: Client = Depends(get_current_client),
):
    """
    Save confirmed lab results. Accepts the LabOCRResult (possibly user-edited)
    returned from /labs/upload.
    """
    saved = []
    for marker in payload.markers:
        lab = LabResult(
            client_id=client.id,
            marker_name=marker.marker_name,
            value=marker.value,
            value_text=marker.value_text,
            unit=marker.unit,
            ref_range_low=marker.ref_range_low,
            ref_range_high=marker.ref_range_high,
            optimal_low=marker.optimal_low,
            optimal_high=marker.optimal_high,
            flag=marker.flag,
            test_date=marker.test_date,
            lab_name=marker.lab_name or payload.lab_name,
            source_pdf_url=source_pdf_url,
            notes=marker.notes,
        )
        db.add(lab)
        saved.append(lab)

    await db.commit()
    for lab in saved:
        await db.refresh(lab)
    return saved


@router.post("", response_model=LabResultResponse, status_code=status.HTTP_201_CREATED)
async def create_lab_result(
    marker: LabResultCreate,
    db: AsyncSession = Depends(get_db),
    client: Client = Depends(get_current_client),
):
    """Manually create a single lab result."""
    lab = LabResult(client_id=client.id, **marker.model_dump())
    db.add(lab)
    await db.commit()
    await db.refresh(lab)
    return lab


@router.delete("/{lab_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lab_result(
    lab_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    client: Client = Depends(get_current_client),
):
    result = await db.execute(
        select(LabResult).where(LabResult.id == lab_id, LabResult.client_id == client.id)
    )
    lab = result.scalars().first()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab result not found.")
    await db.delete(lab)
    await db.commit()
