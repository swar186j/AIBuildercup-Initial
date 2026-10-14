"""Maadhyam FastAPI application factory."""
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from maadhyam_api.routes.advanced_planning import PlanningRequest, plan
from maadhyam_api.config import get_settings
from maadhyam_api.routes.gemini import router as gemini_router
from maadhyam_api.routes.intelligence import router as intelligence_router
from maadhyam_api.routes.extraction import router as extraction_router
from maadhyam_api.routes.health import router as health_router
from maadhyam_api.routes.services import router as services_router
from maadhyam_api.routes.passport_rules import router as passport_rules_router
from maadhyam_api.routes.rule_change_impact import router as rule_change_impact_router
from maadhyam_api.routes.citizen_workflows import router as citizen_workflows_router

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description="AI-powered citizen service resolution platform",
        version=settings.app_version,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    @app.exception_handler(HTTPException)
    async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": "http_error", "message": exc.detail}},
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {"field": ".".join(map(str, error["loc"])), "message": error["msg"]}
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "validation_error", "message": "Invalid request data", "details": details}},
        )

    @app.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unexpected API error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "internal_error", "message": "An unexpected server error occurred"}},
        )

    app.include_router(health_router, prefix="/api")
    app.include_router(services_router, prefix="/api")
    app.include_router(gemini_router, prefix="/api")
    app.include_router(extraction_router, prefix="/api")
    app.include_router(passport_rules_router, prefix="/api")
    app.include_router(rule_change_impact_router, prefix="/api")
    app.include_router(intelligence_router, prefix="/api")
    app.include_router(citizen_workflows_router, prefix="/api")

    @app.post('/api/intelligence/advanced-plan')
    def advanced_plan(request: PlanningRequest):
        return plan(request)
    
    return app


app = create_app()
