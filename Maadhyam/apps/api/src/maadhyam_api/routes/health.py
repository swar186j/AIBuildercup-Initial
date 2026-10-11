from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/health", tags=["System"])


class HealthResponse(BaseModel):
    status: str
    application: str
    version: str


@router.get("", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        application="Maadhyam",
        version="0.1.0",
    )