# Import all models here for Alembic to detect them
from app.models.achievement import Achievement  # noqa: F401
from app.models.activity import Activity  # noqa: F401
from app.models.program import Program  # noqa: F401
from app.models.slack_installation import SlackInstallation, SlackState  # noqa: F401
from app.models.user import User  # noqa: F401
