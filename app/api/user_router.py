from typing import Annotated, List

from fastapi import APIRouter, Depends

from app.schemas.user_schema import UserCreate, UserResponse
from app.services.user_service import UserService

router = APIRouter(tags=["User"])


UserServiceDep = Annotated[UserService, Depends()]


@router.get("/users", response_model=List[UserResponse])
async def get_users(service: UserServiceDep):
    return await service.find_all()


@router.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate, service: UserServiceDep):
    return await service.create(user)
