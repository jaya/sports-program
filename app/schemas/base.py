from app.core.database import Base

# Import all models here for Alembic to detect them
from app.schemas.user import User
from app.schemas.activity import Activity