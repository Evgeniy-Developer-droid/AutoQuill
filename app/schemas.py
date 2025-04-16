from typing import Any, Optional, List, Dict
from pydantic import BaseModel, field_validator


class SuccessResponseSchema(BaseModel):
    message: str


class PaginationSchema(BaseModel):
    page: int
    limit: int
    total: int
    data: List[Dict]