from datetime import datetime
from sqlalchemy import ForeignKey, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.posts.models import Post


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    channel_type: Mapped[str] = mapped_column(nullable=False)  # e.g. "telegram", "discord", "api", and so on
    config_json: Mapped[dict] = mapped_column(JSON, nullable=False)  # JSON config for the channel
    created_at: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())

    company: Mapped["Company"] = relationship(back_populates="channels", lazy="selectin")
    posts: Mapped["Post"] = relationship(back_populates="channel", lazy="selectin")