from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserPublic(BaseModel):
    """Public user representation."""

    id: int = Field(..., description="User ID")
    email: EmailStr = Field(..., description="Email address")
    username: Optional[str] = Field(None, description="Optional username")
    is_active: bool = Field(..., description="Is the account active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")

    class Config:
        from_attributes = True
