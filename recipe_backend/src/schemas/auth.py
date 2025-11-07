from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """JWT token response."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


class LoginRequest(BaseModel):
    """Login credentials."""

    email: EmailStr = Field(..., description="Email")
    password: str = Field(..., description="Password (plaintext)")
