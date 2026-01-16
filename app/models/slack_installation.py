from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SlackInstallation(Base):
    __tablename__ = "slack_installations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    team_id: Mapped[str] = mapped_column(String, index=True, nullable=True)
    enterprise_id: Mapped[str] = mapped_column(String, nullable=True)
    bot_token: Mapped[str] = mapped_column(String, nullable=False)
    bot_id: Mapped[str] = mapped_column(String, nullable=True)
    bot_user_id: Mapped[str] = mapped_column(String, nullable=True)
    installer_user_id: Mapped[str] = mapped_column(String, nullable=True)
    scope: Mapped[str] = mapped_column(String, nullable=True)
    is_enterprise_install: Mapped[bool] = mapped_column(Boolean, default=False)
    installed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class SlackState(Base):
    __tablename__ = "slack_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    state: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    expire_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
