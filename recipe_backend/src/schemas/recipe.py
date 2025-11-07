from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict


class RecipeBase(BaseModel):
    title: str = Field(..., description="Recipe title")
    description: Optional[str] = Field(None, description="Recipe description")
    ingredients: Optional[List[str]] = Field(default=None, description="List of ingredients")
    steps: Optional[List[str]] = Field(default=None, description="List of preparation steps")
    tags: Optional[List[str]] = Field(default=None, description="Tags for the recipe")
    # Expose 'metadata' publicly while mapping from ORM attribute 'recipe_metadata'
    # validation_alias enables reading from ORM attribute; serialization_alias ensures output key remains 'metadata'
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata",
        validation_alias="recipe_metadata",
        serialization_alias="metadata",
    )
    avg_rating: Optional[float] = Field(default=None, description="Average rating")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class RecipeCreate(RecipeBase):
    pass


class RecipeUpdate(BaseModel):
    title: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    ingredients: Optional[List[str]] = Field(default=None)
    steps: Optional[List[str]] = Field(default=None)
    tags: Optional[List[str]] = Field(default=None)
    # Accept 'metadata' field in requests normally
    metadata: Optional[Dict[str, Any]] = Field(default=None)

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class RecipeOut(RecipeBase):
    id: int = Field(..., description="Recipe ID")
    owner_id: int = Field(..., description="Owner user id")

    model_config = ConfigDict(from_attributes=True)


class RatingCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating score 1..5")
    comment: Optional[str] = Field(default=None, description="Optional comment")
