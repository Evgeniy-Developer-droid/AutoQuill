from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, EmailStr, field_validator
from enum import Enum


class UserRole(str, Enum):
    OWNER = "owner"
    EDITOR = "editor"


class UserSettingsSchema(BaseModel):
    id: int


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

