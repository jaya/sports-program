from sqlalchemy import String, Integer, DateTime, func, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.core.database import Base


class Achievement(Base):
    __tablename__ = "achievements"
    __table_args__ = (
        Index(
            'ix_achievements_user_program_cycle',
            'user_id',
            'program_id',
            'cycle_reference',
            unique=True
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False)
    program_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("programs.id"), nullable=False)
    cycle_reference: Mapped[str] = mapped_column(String, nullable=False)
    is_notified: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="achievements")
    program = relationship("Program", back_populates="achievements")
