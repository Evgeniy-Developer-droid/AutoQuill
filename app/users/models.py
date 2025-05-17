import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, DateTime, String
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.channels.models import Channel
from app.ai.models import Source
from app.database import Base
from app.billing.models import  Plan, Usage, Referral, Payment


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())

    current_plan_id: Mapped[Optional[int]] = mapped_column(ForeignKey("plans.id", ondelete="SET NULL"), nullable=True)
    plan_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(), nullable=True)
    balance_tokens: Mapped[int] = mapped_column(default=0)
    referral_code: Mapped[str] = mapped_column(String, nullable=True)
    referred_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)
    last_payment_at: Mapped[Optional[datetime]] = mapped_column(DateTime(), nullable=True)
    subscription_valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(), nullable=True)
    payment_service: Mapped[str] = mapped_column(String, nullable=True)  # "stripe", "paypal", etc.

    users: Mapped["User"] = relationship(back_populates="company", lazy="selectin")
    channels: Mapped["Channel"] = relationship(back_populates="company", lazy="selectin")
    sources: Mapped["Source"] = relationship(back_populates="company", lazy="selectin")
    current_plan: Mapped["Plan"] = relationship(back_populates="companies", lazy="selectin")
    referrals: Mapped["Referral"] = relationship("Referral", back_populates="referrer", lazy="selectin",
                                                 foreign_keys="Referral.referrer_id")
    referred: Mapped["Referral"] = relationship("Referral", back_populates="referred", lazy="selectin",
                                                foreign_keys="Referral.referred_id")
    usages: Mapped["Usage"] = relationship("Usage", back_populates="company", lazy="selectin")
    payments: Mapped["Payment"] = relationship("Payment", back_populates="company", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Company(id={self.id}, name={self.name}, created_at={self.created_at})>"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    password: Mapped[str] = mapped_column(nullable=True)
    full_name: Mapped[str] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(default=False)
    role: Mapped[str] = mapped_column(nullable=True, default="owner")
    is_superuser: Mapped[bool] = mapped_column(default=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
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
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    timezone: Mapped[str] = mapped_column(nullable=True, server_default="UTC")
    user: Mapped["User"] = relationship(back_populates="settings")

