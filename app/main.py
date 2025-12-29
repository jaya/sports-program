from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

from app.exceptions.business import (
    BusinessException,
    EntityNotFoundError,
    DatabaseError,
    BusinessRuleViolationError,
    DuplicateEntityError
)
from app.api.health import router as health_router
from app.api.user import router as user_router
from app.api.activity import router as activity_router
from app.api.program import router as program_router
from app.core.config import settings


def setup_exception_handlers(app: FastAPI):

    @app.exception_handler(EntityNotFoundError)
    async def not_found_handler(request, exc):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": exc.message}
        )

    @app.exception_handler(DuplicateEntityError)
    async def duplicate_handler(request, exc):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": exc.message}
        )

    @app.exception_handler(BusinessRuleViolationError)
    async def business_rule_violation_handler(request, exc):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.message}
        )

    @app.exception_handler(DatabaseError)
    async def db_error_handler(request, exc):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": exc.message}
        )

    @app.exception_handler(BusinessException)
    async def general_business_handler(request, exc):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.message}
        )


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)

app.include_router(health_router)
app.include_router(user_router)
app.include_router(activity_router)
app.include_router(program_router)
setup_exception_handlers(app)


@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.APP_NAME}"}
