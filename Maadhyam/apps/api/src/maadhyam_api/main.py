from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from maadhyam_api.routes.health import router as health_router
from maadhyam_api.routes.services import router as services_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Maadhyam API",
        description="AI-powered citizen service resolution platform",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_methods=["GET"],
        allow_headers=["Content-Type"],
    )

    app.include_router(health_router, prefix="/api")
    app.include_router(services_router, prefix="/api")

    return app


app = create_app()