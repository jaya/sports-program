import time
import structlog
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.api.activity_router import router as activity_router
from app.api.health import router as health_router
from app.api.program_router import router as program_router
from app.api.slack_router import router as slack_router
from app.api.user_router import router as user_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.exceptions.business import (
    BusinessException,
    BusinessRuleViolationError,
    DatabaseError,
    DuplicateEntityError,
    EntityNotFoundError,
)

logger = structlog.get_logger()
setup_logging()

def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(EntityNotFoundError)
    async def not_found_handler(request: Request, exc: EntityNotFoundError):
        logger.warning("entity_not_found", entity=exc.message)
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, content={"detail": exc.message}
        )

    @app.exception_handler(DuplicateEntityError)
    async def duplicate_handler(request: Request, exc: DuplicateEntityError):
        logger.warning("duplicate_entity", detail=exc.message)
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT, content={"detail": exc.message}
        )

    @app.exception_handler(BusinessRuleViolationError)
    async def business_rule_violation_handler(request: Request, exc: BusinessRuleViolationError):
        logger.warning("business_rule_violation", detail=exc.message)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.message},
        )

    @app.exception_handler(DatabaseError)
    async def db_error_handler(request: Request, exc: DatabaseError):
        logger.error("database_error", detail=exc.message)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": exc.message},
        )

    @app.exception_handler(BusinessException)
    async def general_business_handler(request: Request, exc: BusinessException):
        logger.warning("business_exception", detail=exc.message)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"detail": exc.message}
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("unhandled_exception", error=str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected error occurred."},
        )


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)

app.add_middleware(CorrelationIdMiddleware)

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    structlog.contextvars.clear_contextvars()
    
    # Adicionar correlation_id ao contexto se disponível (do middleware anterior)
    request_id = request.headers.get("X-Request-ID")
    if request_id:
        structlog.contextvars.bind_contextvars(request_id=request_id)

    start_time = time.perf_counter()
    
    logger.info(
        "request_started",
        method=request.method,
        path=request.url.path,
        query_params=str(request.query_params),
        client_ip=request.client.host if request.client else None,
    )

    try:
        response = await call_next(request)
    except Exception as e:
        process_time = time.perf_counter() - start_time
        logger.error(
            "request_failed",
            method=request.method,
            path=request.url.path,
            error=str(e),
            duration=f"{process_time:.4f}s",
        )
        raise e

    process_time = time.perf_counter() - start_time
    logger.info(
        "request_finished",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration=f"{process_time:.4f}s",
    )
    
    return response


app.include_router(health_router)
app.include_router(user_router)
app.include_router(activity_router)
app.include_router(program_router)
app.include_router(slack_router)
setup_exception_handlers(app)


@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.APP_NAME}"}
