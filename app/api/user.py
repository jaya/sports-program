from fastapi import APIRouter, Depends
from typing import List, Annotated

from app.schemas.user import UserCreate, UserResponse
from app.services.users.find_all import FindAll
from app.services.users.create import Create

router = APIRouter(tags=["User"])

FindAllServiceDep = Annotated[FindAll, Depends()]
CreateServiceDep = Annotated[Create, Depends()]


@router.get("/users", response_model=List[UserResponse])
async def get_users(service: FindAllServiceDep):
    return await service.execute()


@router.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate, service: CreateServiceDep):
    return await service.execute(user)
