from datetime import datetime
from typing import List, Optional

from sqlalchemy import ForeignKey, DateTime, JSON, select, String
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from app.database import Base
from app.posts.models import Post
from app.ai.models import Source, AIConfig, ScheduledAIPost
from app.database import async_session_maker


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(nullable=False, server_default="Channel")
    channel_type: Mapped[str] = mapped_column(nullable=False)  # e.g. "telegram", "discord", "api", and so on
    config_json: Mapped[dict] = mapped_column(JSON, nullable=False)  # JSON config for the channel
    created_at: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())

    company: Mapped["Company"] = relationship(back_populates="channels", lazy="selectin")
    posts: Mapped[List[Post]] = relationship(back_populates="channel", lazy="selectin")
    logs: Mapped["ChannelLog"] = relationship(back_populates="channel", lazy="selectin")
    sources: Mapped["Source"] = relationship(back_populates="channel", lazy="selectin")
    ai_config: Mapped["AIConfig"] = relationship(back_populates="channel", lazy="selectin")
    scheduled_ai_posts: Mapped["ScheduledAIPost"] = relationship(back_populates="channel", lazy="selectin")


class ChannelLog(Base):
    __tablename__ = "channel_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"))
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), nullable=True)
    message: Mapped[str] = mapped_column(nullable=False)
    action: Mapped[str] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())

    channel: Mapped["Channel"] = relationship(back_populates="logs", lazy="selectin")
    post: Mapped["Post"] = relationship(back_populates="logs", lazy="selectin")