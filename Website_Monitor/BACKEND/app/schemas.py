# backend/app/schemas.py
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional
from datetime import datetime

class WebsiteIn(BaseModel):
    name: str
    url: HttpUrl
    ownerEmail: Optional[str] = None
    interval: int = Field(60, gt=0)  # seconds
    active: bool = True

class WebsiteOut(WebsiteIn):
    id: str

class CheckOut(BaseModel):
    websiteId: str
    status: str
    httpStatus: Optional[int] = None
    responseTimeMs: Optional[int] = None
    error: Optional[str] = None
    checkedAt: datetime
