from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, UploadFile

from app.core.deps import get_current_user
from app.services.storage import storage_service

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/presigned")
async def create_upload_url(
    content_type: str | None = None,
    _current_user=Depends(get_current_user),
):
    prefix = "tickets/uploads"
    presigned = storage_service.generate_presigned_post(
        key_prefix=prefix,
        content_type=content_type,
    )
    return {"url": presigned.url, "fields": presigned.fields, "file_key": presigned.file_key}


@router.post("/direct")
async def direct_upload(
    file: UploadFile = File(...),
    _current_user=Depends(get_current_user),
):
    safe_name = file.filename or "upload.bin"
    key = f"tickets/uploads/{uuid.uuid4()}-{safe_name}"

    body = await file.read()
    content_type = file.content_type or "application/octet-stream"
    storage_service.upload_bytes(key=key, data=body, content_type=content_type)

    return {"file_key": key}
