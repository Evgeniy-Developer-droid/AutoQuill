from datetime import datetime
from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.users.models import User


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    token: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())
    expired_at: Mapped[datetime] = mapped_column(DateTime())

    user: Mapped["User"] = relationship(back_populates="auth_session", lazy="selectin")
