from sqlalchemy import String, Integer, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import calendar

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
        start_date = datetime(year, month, 1)

        last_day = calendar.monthrange(year, month)[1]
        end_date = datetime(year, month, last_day, 23, 59, 59)

        return cls.performed_at.between(start_date, end_date)
