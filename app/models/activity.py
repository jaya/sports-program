from sqlalchemy import String, Integer, DateTime, func, ForeignKey, extract
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.core.database import Base


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False)
    program_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("programs.id"), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    evidence_url: Mapped[str] = mapped_column(String, nullable=True)
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="activities")
    program = relationship("Program", back_populates="activities")

    @classmethod
    def filter_date_tz(cls, year: int, month: int, tz: str = "America/Sao_Paulo"):
        local_date = func.timezone(tz, cls.performed_at)

        return (
            extract('year', local_date) == year,
            extract('month', local_date) == month
        )
