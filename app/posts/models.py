from datetime import datetime
from sqlalchemy import ForeignKey, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"))
    content: Mapped[str] = mapped_column(nullable=False)  # Content of the post
    ai_generated: Mapped[bool] = mapped_column(default=False)  # Whether the post was AI-generated
    scheduled_time: Mapped[datetime] = mapped_column(DateTime(), nullable=True)  # Time when the post is scheduled to be sent
    created_at: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())  # Time when the post was created
    status: Mapped[str] = mapped_column(nullable=False, default="draft")  # Status of the post (e.g., draft, scheduled, published, failed)

    channel: Mapped["Channel"] = relationship(back_populates="posts", lazy="selectin")
