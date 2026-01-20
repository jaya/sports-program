import time
import structlog
from fastapi import Request

logger = structlog.get_logger()

async def logging_middleware(request: Request, call_next):
    structlog.contextvars.clear_contextvars()

    start_time = time.perf_counter()

    logger.info(
        "request_started",
        method=request.method,
        path=request.url.path,
    )

    response = await call_next(request)

    process_time = time.perf_counter() - start_time
    logger.info(
        "request_finished",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=int(process_time * 1000),
    )

    return response