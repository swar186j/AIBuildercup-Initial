from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.health import router as health_router
from api.routes.evidence import router as evidence_router

app = FastAPI(title="Draft1 API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(health_router, prefix="/api")
app.include_router(evidence_router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Draft1 API", "docs": "/docs", "health": "/api/health"}
