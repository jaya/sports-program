from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.user import router as user_router
from app.api.activity import router as activity_router
from app.api.program import router as program_router
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)

app.include_router(health_router)
app.include_router(user_router)
app.include_router(activity_router)
app.include_router(program_router)


@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.APP_NAME}"}
