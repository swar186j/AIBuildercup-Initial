import os
import uuid
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

router = APIRouter(prefix="/evidence", tags=["evidence"])
MAX_BYTES = 10 * 1024 * 1024
ALLOWED = {"application/pdf": ".pdf", "image/png": ".png", "image/jpeg": ".jpg"}
UPLOAD_DIR = Path(os.environ.get("DRAFT1_UPLOAD_DIR", "data/uploads"))

class SubmissionResponse(BaseModel):
    submission_id: str
    status: Literal["received"] = "received"
    scheme: Literal["ESIC", "PMAY-G", "GENERAL"]
    applicant_name: str
    reference_id: str | None
    filename: str
    note: str = Field(default="Received for review; no eligibility or medical decision has been made.")

@router.post("/submit", response_model=SubmissionResponse, status_code=201)
async def submit_evidence(
    scheme: Annotated[Literal["ESIC", "PMAY-G", "GENERAL"], Form()],
    applicant_name: Annotated[str, Form(min_length=1, max_length=200)],
    document: Annotated[UploadFile, File()],
    reference_id: Annotated[str | None, Form(max_length=100)] = None,
):
    if document.content_type not in ALLOWED:
        raise HTTPException(415, "Only PDF, PNG, and JPEG documents are supported")
    submission_id = uuid.uuid4().hex
    suffix = ALLOWED[document.content_type]
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    destination = UPLOAD_DIR / f"{submission_id}{suffix}"
    size = 0
    try:
        with destination.open("wb") as out:
            while chunk := await document.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_BYTES:
                    raise HTTPException(413, "Maximum document size is 10 MB")
                out.write(chunk)
        if size == 0:
            raise HTTPException(400, "Document is empty")
        with destination.open("rb") as source:
            signature = source.read(8)
        valid = (
            suffix == ".pdf" and signature.startswith(b"%PDF-")
            or suffix == ".png" and signature.startswith(b"\x89PNG\r\n\x1a\n")
            or suffix == ".jpg" and signature.startswith(b"\xff\xd8\xff")
        )
        if not valid:
            raise HTTPException(415, "Document content does not match its declared type")
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    finally:
        await document.close()
    return SubmissionResponse(
        submission_id=submission_id,
        scheme=scheme,
        applicant_name=applicant_name.strip(),
        reference_id=reference_id,
        filename=Path(document.filename or "document").name,
    )
