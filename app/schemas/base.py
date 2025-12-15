from app.core.database import Base

# Import all models here for Alembic to detect them
from app.schemas.user import User
from app.models.activity import Activity
from app.schemas.program import Program
