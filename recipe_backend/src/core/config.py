import os
from functools import lru_cache
from typing import List, Optional

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Application settings loaded from environment variables."""

    APP_ENV: str = Field(default=os.getenv("APP_ENV", "development"), description="Application environment.")
    SECRET_KEY: str = Field(default=os.getenv("SECRET_KEY", "CHANGE_ME_DEV_SECRET"), description="JWT secret key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")), description="Access token expiry in minutes"
    )
    CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: [
            o.strip()
            for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
            if o.strip()
        ],
        description="Allowed CORS origins",
    )
    DATABASE_URL: Optional[str] = Field(default=os.getenv("DATABASE_URL"), description="DB connection string")

    class Config:
        arbitrary_types_allowed = True


# PUBLIC_INTERFACE
@lru_cache()
def get_settings() -> Settings:
    """Return cached Settings object populated from environment variables."""
    return Settings()
