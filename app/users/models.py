from datetime import datetime
from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.channels.models import Channel
from app.ai.models import Source
from app.database import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())

    users: Mapped["User"] = relationship(back_populates="company", lazy="selectin")
    channels: Mapped["Channel"] = relationship(back_populates="company", lazy="selectin")
    sources: Mapped["Source"] = relationship(back_populates="company", lazy="selectin")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    password: Mapped[str] = mapped_column(nullable=True)
    full_name: Mapped[str] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(default=False)
    role: Mapped[str] = mapped_column(nullable=True, default="owner")
    is_superuser: Mapped[bool] = mapped_column(default=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())
    last_login: Mapped[datetime] = mapped_column(DateTime(), nullable=True)

    settings: Mapped["UserSetting"] = relationship(
        back_populates="user", lazy="selectin"
    )
    auth_session: Mapped["AuthSession"] = relationship(back_populates="user")
    company = relationship("Company", back_populates="users", lazy="selectin")


class UserSetting(Base):
    __tablename__ = "users_setting"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    timezone: Mapped[str] = mapped_column(nullable=True, server_default="UTC")
    user: Mapped["User"] = relationship(back_populates="settings")

