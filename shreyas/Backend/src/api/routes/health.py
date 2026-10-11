from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health")
def health():
    return {"status": "healthy", "application": "Draft1", "version": "0.1.0"}
