from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .session import Base, engine


def _is_sqlite() -> bool:
    """
    Determine whether the active engine is SQLite.
    """
    return engine.url.get_backend_name() == "sqlite"


# Choose appropriate column types based on backend
if _is_sqlite():
    JSONType = JSONB  # type: ignore[assignment]
    # For SQLite, SQLAlchemy will fallback JSONB to a generic JSON if available, else Text
    # But to be explicit, we can store JSON as Text and let Pydantic handle conversion.
    # However, SQLAlchemy 2.0 bundles JSON type; use Text as safer generic for legacy SQLite.
    from sqlalchemy import JSON as SA_JSON  # available for SQLite as TEXT-encoded JSON
    JSONType = SA_JSON  # type: ignore[assignment]

    def ArrayOfString():
        # SQLite does not support ARRAY; store as JSON list of strings
        return JSONType
else:
    JSONType = JSONB  # Native JSONB for Postgres
    def ArrayOfString():
        return ARRAY(String)


class User(Base):
    """
    User accounts for authentication and ownership of recipes/ratings.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(50), unique=True, index=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    recipes: Mapped[List["Recipe"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    ratings: Mapped[List["RecipeRating"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Recipe(Base):
    """
    Recipes created by users.
    """
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ingredients: Mapped[List[str] | None] = mapped_column(ArrayOfString(), nullable=True)
    steps: Mapped[List[str] | None] = mapped_column(ArrayOfString(), nullable=True)
    tags: Mapped[List[str] | None] = mapped_column(ArrayOfString(), nullable=True)
    # Use a non-reserved attribute name for JSON metadata.
    # Keep the database column name as 'recipe_metadata' (new) since there is no migration system here.
    recipe_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONType, nullable=True)
    avg_rating: Mapped[Optional[float]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    owner: Mapped["User"] = relationship(back_populates="recipes")
    ratings: Mapped[List["RecipeRating"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan"
    )


class RecipeRating(Base):
    """
    Ratings given by users to recipes.
    """
    __tablename__ = "recipe_ratings"
    __table_args__ = (
        UniqueConstraint("user_id", "recipe_id", name="uq_user_recipe_rating"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"), index=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1..5 typical
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="ratings")
    recipe: Mapped["Recipe"] = relationship(back_populates="ratings")
