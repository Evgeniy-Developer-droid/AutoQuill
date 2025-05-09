from datetime import datetime
from sqlalchemy import ForeignKey, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"))
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    source_type: Mapped[str] = mapped_column(nullable=False, server_default="file") # file, document
    source_metadata: Mapped[dict] = mapped_column(JSON, nullable=False)
    document_id: Mapped[str] = mapped_column(nullable=False)

    channel: Mapped["Channel"] = relationship(back_populates="sources")
    company: Mapped["Company"] = relationship(back_populates="sources")


class AIConfig(Base):
    __tablename__ = "ai_config"

    id: Mapped[int] = mapped_column(primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"))
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    temperature: Mapped[float] = mapped_column(nullable=False, server_default="0") # 0-1
    max_tokens: Mapped[int] = mapped_column(nullable=False, server_default="1000") # 0-4096 max answer length
    language: Mapped[str] = mapped_column(nullable=False, server_default="en")  # en, es, fr, de, it, pt, ru, zh, ja, ko
    tone: Mapped[str] = mapped_column(nullable=False, server_default="neutral")  # neutral, formal, informal, friendly, professional
    writing_style: Mapped[str] = mapped_column(nullable=False, server_default="concise")  # concise, detailed, persuasive, informative
    emojis: Mapped[bool] = mapped_column(nullable=False, server_default="false")  # true, false
    custom_instructions: Mapped[str] = mapped_column(nullable=False, server_default="")  # custom instructions for the AI

    channel: Mapped["Channel"] = relationship(back_populates="ai_config")
