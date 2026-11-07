
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ClaimCreate(BaseModel):
    item_id: int
    message: str = Field(
        min_length=10,
        max_length=1000,
        description="Explain why you believe this item belongs to you."
    )


class ClaimResponse(BaseModel):
    id: int
    item_id: int
    claimant_id: int
    message: str
    status: str
    owner_response: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ClaimReview(BaseModel):
    status: str = Field(
        pattern="^(approved|rejected)$"
    )
    owner_response: str | None = Field(
        default=None,
        max_length=1000
    )
