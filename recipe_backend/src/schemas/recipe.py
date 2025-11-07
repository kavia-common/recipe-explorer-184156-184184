from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RecipeBase(BaseModel):
    title: str = Field(..., description="Recipe title")
    description: Optional[str] = Field(None, description="Recipe description")
    ingredients: Optional[List[str]] = Field(default=None, description="List of ingredients")
    steps: Optional[List[str]] = Field(default=None, description="List of preparation steps")
    tags: Optional[List[str]] = Field(default=None, description="Tags for the recipe")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    avg_rating: Optional[float] = Field(default=None, description="Average rating")


class RecipeCreate(RecipeBase):
    pass


class RecipeUpdate(BaseModel):
    title: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    ingredients: Optional[List[str]] = Field(default=None)
    steps: Optional[List[str]] = Field(default=None)
    tags: Optional[List[str]] = Field(default=None)
    metadata: Optional[Dict[str, Any]] = Field(default=None)


class RecipeOut(RecipeBase):
    id: int = Field(..., description="Recipe ID")
    owner_id: int = Field(..., description="Owner user id")

    class Config:
        from_attributes = True


class RatingCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating score 1..5")
    comment: Optional[str] = Field(default=None, description="Optional comment")
