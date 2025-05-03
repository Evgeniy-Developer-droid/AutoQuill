from typing import Optional, Dict, Any, Literal

from pydantic import BaseModel


class DocumentInSchema(BaseModel):
    text: Optional[str]


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
    total_count: int

    class Config:
        orm_mode = True
        use_enum_values = True

