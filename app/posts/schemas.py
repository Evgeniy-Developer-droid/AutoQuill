from typing import Optional, List, Literal
import pytz
from pydantic import BaseModel, field_validator, field_serializer
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
    timezone: Optional[str] = None

    class Config:
        orm_mode = True
        use_enum_values = True

    @field_serializer("scheduled_time")
    def serialize_scheduled_time(self, value: datetime) -> Optional[datetime]:
        if value:
            print(f"Original scheduled_time: {value}")
            # change utc to local time
            user_tz = pytz.timezone(self.timezone or "UTC")
            print(f"User timezone: {user_tz}")
            local_time = value.astimezone(user_tz)
            print(f"Localized scheduled_time: {local_time}")
            return local_time.replace(tzinfo=None)
        return None


class PostInSchema(BaseModel):
    channel_id: int
    content: str
    ai_generated: bool = False
    scheduled_time: Optional[datetime] = None
    timezone: Optional[str] = None
    status: Literal['draft', 'scheduled'] = 'draft'

    class Config:
        orm_mode = True
        use_enum_values = True

    @field_validator("timezone", mode="before")
    def validate_timezone(cls, value):
        if value and value not in pytz.all_timezones:
            raise ValueError(f"Invalid timezone")
        return value


class PostUpdateSchema(BaseModel):
    content: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    timezone: Optional[str] = None
    status: Optional[Literal['draft', 'scheduled']] = None

    class Config:
        orm_mode = True
        use_enum_values = True

    @field_validator("timezone", mode="before")
    def validate_timezone(cls, value):
        if value and value not in pytz.all_timezones:
            raise ValueError(f"Invalid timezone: {value}")
        return value


class PostListSchema(BaseModel):
    posts: List[PostOutSchema]
    total: int

    class Config:
        orm_mode = True
        use_enum_values = True

