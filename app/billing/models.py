from datetime import datetime

from sqlalchemy import ForeignKey, DateTime, JSON, select, String, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class ActionType(Enum):
    POST = "post"
    AI = "ai"


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[int] = mapped_column()
    send_post_limit: Mapped[int] = mapped_column()
    ai_generation_limit: Mapped[int] = mapped_column()
    channels_limit: Mapped[int] = mapped_column()
    ai_enabled: Mapped[bool] = mapped_column(default=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_trial: Mapped[bool] = mapped_column(default=False)

    companies: Mapped["Company"] = relationship(back_populates="current_plan", lazy="selectin")


class Usage(Base):
    __tablename__ = "usages"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    action_type: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())

    company: Mapped["Company"] = relationship(back_populates="usages", lazy="selectin")


class Referral(Base):
    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(primary_key=True)
    referrer_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    referred_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    reward_given: Mapped[bool] = mapped_column(default=False)

    referrer: Mapped["Company"] = relationship(
        "Company", back_populates="referrals", foreign_keys=[referrer_id], lazy="selectin"
    )
    referred: Mapped["Company"] = relationship(
        "Company", back_populates="referred", foreign_keys=[referred_id], lazy="selectin"
    )


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    order_id: Mapped[str] = mapped_column(nullable=True)
    amount: Mapped[int] = mapped_column()
    description: Mapped[str] = mapped_column()
    is_successful: Mapped[bool] = mapped_column(default=False)
    payment_service: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())

    company: Mapped["Company"] = relationship(back_populates="payments", lazy="selectin")

