from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, EmailStr, field_validator
from enum import Enum


class UserRole(str, Enum):
    OWNER = "owner"
    EDITOR = "editor"


class UserSettingsSchema(BaseModel):
    id: int
    timezone: Optional[str]


class UserSchema(BaseModel):
    id: int
    full_name: Optional[str] = None
    email: EmailStr
    is_active: bool
    role: UserRole = UserRole.OWNER
    created_at: datetime
    last_login: Optional[datetime] = None
    settings: UserSettingsSchema

    class Config:
        orm_mode = True
        use_enum_values = True


class UserUpdateSchema(BaseModel):
    full_name: Optional[str] = None


class DashboardOutSchemas(BaseModel):
    all_channels_count: int
    all_posts_count: int
    all_ai_generated_posts_count: int
    last_channels: list[dict[str, Any]]
    last_posts: list[dict[str, Any]]
    last_channel_logs: list[dict[str, Any]]

    class Config:
        orm_mode = True


class PasswordUpdateSchema(BaseModel):
    old_password: str
    password: str
