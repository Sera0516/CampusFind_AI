from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class ItemCreate(BaseModel):
    title: str = Field(min_length=2, max_length=150)
    description: str = Field(min_length=5)
    item_type: str
    category: str
    location: str
    event_date: datetime
    image_url: Optional[str] = None

class ItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    item_type: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    event_date: Optional[datetime] = None
    image_url: Optional[str] = None

class ItemResponse(BaseModel):
    id: int
    title: str
    description: str
    item_type: str
    category: str
    location: str
    event_date: datetime
    image_url: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
