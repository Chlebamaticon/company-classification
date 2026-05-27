"""POST /submissions and GET /submissions/{id}."""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy import text

from salespatriot_shared.messages import ClassifyRequest, Envelope
from salespatriot_shared.mq import ROUTING_CLASSIFY, publish

router = APIRouter(prefix="/submissions", tags=["submissions"])

UPLOADS_DIR = os.environ.get("UPLOADS_DIR", "/data/uploads")


@router.post("", status_code=202)
async def create_submission(
    request: Request,
    company_name: str = Form(...),
    website_url: str = Form(...),
    email_domain: str | None = Form(None),
    file: UploadFile | None = File(None),
):
    sid = uuid.uuid4()
    file_path: str | None = None

    if file and file.filename:
        upload_dir = Path(UPLOADS_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = str(upload_dir / f"{sid}.pdf")
        content = await file.read()
        Path(file_path).write_bytes(content)

    engine = request.app.state.db
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO submissions (id, company_name, website_url, email_domain, file_path) "
                "VALUES (:id, :cn, :wu, :ed, :fp)"
            ),
            {"id": str(sid), "cn": company_name, "wu": website_url, "ed": email_domain, "fp": file_path},
        )

    envelope = Envelope[ClassifyRequest](
        submission_id=sid,
        trace_id=uuid.uuid4(),
        payload=ClassifyRequest(
            company_name=company_name,
            website_url=website_url,
            email_domain=email_domain,
            has_document=file_path is not None,
        ),
    )
    channel = request.app.state.mq_channel
    await publish(channel, ROUTING_CLASSIFY, envelope)

    return JSONResponse(
        status_code=202,
        content={"submission_id": str(sid), "status": "queued"},
    )


@router.get("/{submission_id}")
async def get_submission(request: Request, submission_id: uuid.UUID):
    engine = request.app.state.db
    async with engine.connect() as conn:
        row = (
            await conn.execute(
                text("SELECT id, company_name, website_url, email_domain, file_path, status, created_at FROM submissions WHERE id = :id"),
                {"id": str(submission_id)},
            )
        ).mappings().first()

    if not row:
        raise HTTPException(404, "submission not found")

    result: dict[str, Any] = {
        "submission_id": str(row["id"]),
        "company_name": row["company_name"],
        "website_url": row["website_url"],
        "email_domain": row["email_domain"],
        "status": row["status"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "fsc_codes": None,
    }

    async with engine.connect() as conn:
        cls_row = (
            await conn.execute(
                text("SELECT fsc_codes FROM classifications WHERE submission_id = :id ORDER BY created_at DESC LIMIT 1"),
                {"id": str(submission_id)},
            )
        ).mappings().first()

    if cls_row:
        result["fsc_codes"] = cls_row["fsc_codes"]

    return result
