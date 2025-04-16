from typing import Optional, List

from pydantic import BaseModel, field_validator
from enum import Enum
from datetime import datetime


class PostStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


class PostOutSchema(BaseModel):
    id: int
    company_id: int
    channel_id: int
    content: str
    ai_generated: bool = False
    scheduled_time: Optional[datetime] = None
    created_at: datetime
    status: PostStatus

    class Config:
        orm_mode = True
        use_enum_values = True


class PostInSchema(BaseModel):
    channel_id: int
    content: str
    ai_generated: bool = False
    scheduled_time: Optional[datetime] = None

    class Config:
        orm_mode = True
        use_enum_values = True

    @field_validator("scheduled_time", mode="after")
    def validate_scheduled_time(cls, value):
        value = value.replace(tzinfo=None) if value else None
        if value and value < datetime.now():
            raise ValueError("Scheduled time cannot be in the past.")
        return value


class PostUpdateSchema(BaseModel):
    content: Optional[str] = None
    ai_generated: Optional[bool] = None
    scheduled_time: Optional[datetime] = None

    class Config:
        orm_mode = True
        use_enum_values = True

    @field_validator("scheduled_time", mode="after")
    def validate_scheduled_time(cls, value):
        value = value.replace(tzinfo=None) if value else None
        if value and value < datetime.now():
            raise ValueError("Scheduled time cannot be in the past.")
        return value


class PostListSchema(BaseModel):
    posts: List[PostOutSchema]
    total: int

    class Config:
        orm_mode = True
        use_enum_values = True

