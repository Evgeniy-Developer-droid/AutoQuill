from datetime import datetime
from typing import Optional, Dict, Any, Literal, List

from pydantic import BaseModel, field_validator


class DocumentInSchema(BaseModel):
    text: str
    title: str



class ES_Document(BaseModel):
    id: str
    document_id: str
    title: Optional[str]
    text: str
    timestamp: Optional[str]
    channel_id: int
    company_id: int
    page: Optional[int] = 0
    embedding: Optional[list[float]] = None
    metadata: Optional[Dict[str, Any]] = None


class SourcesInSchema(BaseModel):
    source_type: Literal["file", "document"]
    source_metadata: dict
    document_id: str
    channel_id: int
    company_id: int


class SourcesOutSchema(BaseModel):
    id: int
    channel_id: int
    company_id: int
    source_type: Literal["file", "document"]
    source_metadata: dict
    document_id: str


class SourcesListSchema(BaseModel):
    sources: list[SourcesOutSchema]
    total: int

    class Config:
        orm_mode = True
        use_enum_values = True


class GeneratePostsInSchema(BaseModel):
    topic: Optional[str] = None


class AIConfigOutSchema(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    temperature: float
    max_tokens: int
    language: str
    tone: str
    writing_style: str
    emojis: bool
    custom_instructions: str


class AIConfigUpdateSchema(BaseModel):
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    language: Optional[Literal["en", "de", "es", "fr", "it", "ua", "ru"]] = None
    tone: Optional[Literal["neutral", "formal", "informal", "friendly", "professional"]] = None
    writing_style: Optional[Literal["concise", "detailed", "persuasive", "informative"]] = None
    emojis: Optional[bool] = None
    custom_instructions: Optional[str] = None

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, value):
        if value is None:
            return None
        if not (0 <= value <= 1):
            raise ValueError("Temperature must be between 0 and 1.")
        return value

    @field_validator("max_tokens")
    @classmethod
    def validate_max_tokens(cls, value):
        if value is None:
            return None
        if not (0 <= value <= 4096):
            raise ValueError("Max tokens must be between 0 and 4096.")
        return value


class ScheduledAIPostInSchema(BaseModel):
    weekdays: List[int]  # [0, 1, 2, 3, 4, 5, 6] for all days
    times: List[str]  # ["08:00", "12:00", "18:00"]
    is_active: bool = True
    timezone: Optional[str] = None

    @field_validator("weekdays")
    @classmethod
    def validate_weekdays(cls, value):
        if not all(0 <= day <= 6 for day in value):
            raise ValueError("Weekdays must be between 0 and 6.")
        return value

    @field_validator("times")
    @classmethod
    def validate_times(cls, value):
        if not all(isinstance(time, str) and len(time) == 5 and time[2] == ":" for time in value):
            raise ValueError("Times must be in HH:MM format.")
        return value


class ScheduledAIPostOutSchema(BaseModel):
    id: int
    weekdays: List[int]  # [0, 1, 2, 3, 4, 5, 6] for all days
    times: List[str]  # ["08:00", "12:00", "18:00"]
    is_active: bool = True
    last_run_at: datetime

    class Config:
        orm_mode = True
        use_enum_values = True

