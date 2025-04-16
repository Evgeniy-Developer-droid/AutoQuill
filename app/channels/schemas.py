from typing import Optional, List

from pydantic import BaseModel
from enum import Enum
from datetime import datetime


class ChannelType(str, Enum):
    TELEGRAM = "telegram"
    API = "api"


class ChannelOutSchema(BaseModel):
    id: int
    company_id: int
    channel_type: ChannelType
    config_json: Optional[dict] = None
    created_at: datetime

    class Config:
        orm_mode = True
        use_enum_values = True


class ChannelInSchema(BaseModel):
    channel_type: ChannelType
    config_json: Optional[dict] = None

    class Config:
        orm_mode = True
        use_enum_values = True


class ChannelUpdateSchema(BaseModel):
    channel_type: Optional[ChannelType] = None
    config_json: Optional[dict] = None

    class Config:
        orm_mode = True
        use_enum_values = True


class ChannelListSchema(BaseModel):
    channels: List[ChannelOutSchema]
    total: int

    class Config:
        orm_mode = True
        use_enum_values = True


