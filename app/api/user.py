from fastapi import APIRouter, Depends
from typing import List, Annotated

from app.models.user import UserCreate, UserRead
from app.services.user import UserService

router = APIRouter(tags=["User"])

UserServiceDep = Annotated[UserService, Depends()]

@router.get("/users", response_model=List[UserRead])
async def get_users(service: UserServiceDep):
    return await service.find_all_users()


@router.post("/users", response_model=UserRead)
async def create_user(user: UserCreate, service: UserServiceDep):
    return await service.insert_new_user(user)