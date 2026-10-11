from fastapi import APIRouter

from maadhyam_api.schemas.service import (
    GovernmentService,
    ServiceListResponse,
)

router = APIRouter(prefix="/services", tags=["Government Services"])


@router.get("", response_model=ServiceListResponse)
def list_services() -> ServiceListResponse:
    return ServiceListResponse(
        services=[
            GovernmentService(
                id="passport",
                name="Passport Seva",
                description="Passport documentation and application assistance",
                status="planned",
            ),
            GovernmentService(
                id="aadhaar",
                name="Aadhaar Services",
                description="Identity and address documentation assistance",
                status="planned",
            ),
            GovernmentService(
                id="epfo",
                name="EPFO Services",
                description="Provident fund documentation assistance",
                status="planned",
            ),
        ]
    )