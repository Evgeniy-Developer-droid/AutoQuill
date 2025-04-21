from typing import Optional, List, Literal, Union

from pydantic import BaseModel
from enum import Enum
from datetime import datetime


class ChannelType(str, Enum):
    TELEGRAM = "telegram"
    API = "api"


class TelegramSettings(BaseModel):
    telegram_bot_token: Optional[str] = None
    telegram_channel_id: Optional[str] = None
    parse_mode: Optional[Literal["html", "markdown"]] = None


class ApiSettings(BaseModel):
    method: Optional[str] = None
    url: Optional[str] = None
    headers: Optional[dict] = None
    payload: Optional[dict] = None
    params: Optional[dict] = None


class ChannelOutSchema(BaseModel):
    id: int
    name: str
    company_id: int
    channel_type: ChannelType
    config_json: Optional[Union[TelegramSettings, ApiSettings]] = None
    created_at: datetime

    class Config:
        orm_mode = True
        use_enum_values = True


class ChannelInSchema(BaseModel):
    channel_type: ChannelType
    name: str
    config_json: Optional[Union[TelegramSettings, ApiSettings]] = None

    class Config:
        orm_mode = True
        use_enum_values = True


class ChannelUpdateSchema(BaseModel):
    channel_type: Optional[ChannelType] = None
    name: Optional[str] = None
    config_json: Optional[Union[TelegramSettings, ApiSettings]] = None

    class Config:
        orm_mode = True
        use_enum_values = True


class ChannelListSchema(BaseModel):
    channels: List[ChannelOutSchema]
    total: int

    class Config:
        orm_mode = True
        use_enum_values = True


class ChannelLogOutSchema(BaseModel):
    id: int
    channel_id: int
    post_id: Optional[int] = None
    message: str
    created_at: datetime

    class Config:
        orm_mode = True
        use_enum_values = True


class ChannelLogListSchema(BaseModel):
    logs: List[ChannelLogOutSchema]
    total: int

    class Config:
        orm_mode = True
        use_enum_values = True

