from pydantic import BaseModel


class GovernmentService(BaseModel):
    id: str
    name: str
    description: str
    status: str


class ServiceListResponse(BaseModel):
    services: list[GovernmentService]