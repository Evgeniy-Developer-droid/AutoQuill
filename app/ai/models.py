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

