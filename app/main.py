from contextlib import asynccontextmanager

import structlog
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

from app.api.activity_router import router as activity_router
from app.api.admin_router import router as admin_router
from app.api.health import router as health_router
from app.api.program_router import router as program_router
from app.api.slack_router import router as slack_router
from app.api.user_router import router as user_router
from app.core.config import settings
from app.core.database import engine
from app.core.logging.middleware import logging_middleware
from app.core.logging.setup import setup_logging
from app.core.scheduler import start_scheduler, stop_scheduler
from app.exceptions.business import (
    BusinessException,
    BusinessRuleViolationError,
    DatabaseError,
    DuplicateEntityError,
    EntityNotFoundError,
    ExternalServiceError,
)

logger = structlog.get_logger()
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()
    await engine.dispose()


def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(EntityNotFoundError)
    async def not_found_handler(request, exc):
        logger.warning("Entity not found", detail=exc.message)
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, content={"detail": exc.message}
        )

    @app.exception_handler(DuplicateEntityError)
    async def duplicate_handler(request, exc):
        logger.warning("Duplicate entity", detail=exc.message)
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT, content={"detail": exc.message}
        )

    @app.exception_handler(BusinessRuleViolationError)
    async def business_rule_violation_handler(request, exc):
        logger.warning("Business rule violation", detail=exc.message)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.message},
        )

    @app.exception_handler(DatabaseError)
    async def db_error_handler(request, exc):
        logger.error("Database error occurred", detail=exc.message)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": exc.message},
        )

    @app.exception_handler(ExternalServiceError)
    async def external_service_handler(request, exc):
        logger.error("External service error occurred", detail=exc.message)
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={"detail": exc.message},
        )

    @app.exception_handler(BusinessException)
    async def general_business_handler(request, exc):
        logger.warning("Business exception occurred", detail=str(exc))
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"detail": exc.message}
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request, exc):
        logger.exception(
            "Unhandled server error occurred",
            method=request.method,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected error occurred."},
        )


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.add_middleware(CorrelationIdMiddleware)
app.middleware("http")(logging_middleware)


app.include_router(health_router)
app.include_router(user_router)
app.include_router(activity_router)
app.include_router(program_router)
app.include_router(slack_router)
app.include_router(admin_router)
setup_exception_handlers(app)


@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.APP_NAME}"}
