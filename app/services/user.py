from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import UserCreate
from app.schemas.user import User
from app.core.database import get_db


class UserService:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def find_all_users(self):
        result = await self.db.execute(select(User))
        users = result.scalars().all()
        return users


    async def insert_new_user(self, user: UserCreate):
        user_found = await self.find_user_by_slack_id(user.slack_id)
        if user_found:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="User with this slack_id already exists"
            )

        db_user = User(slack_id=user.slack_id, display_name=user.display_name)
        self.db.add(db_user)
        try:
            await self.db.commit()
            await self.db.refresh(db_user)
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"An error occurred: {str(e)}"
            )
        
        return db_user
    
    async def find_user_by_slack_id(self, slack_id: str):
        stmt = select(User).where(User.slack_id == slack_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()