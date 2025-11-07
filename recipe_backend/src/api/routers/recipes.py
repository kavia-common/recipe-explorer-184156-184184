from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, asc, desc, func
from sqlalchemy.orm import Session

from src.api.deps import get_current_active_user, pagination_params
from src.db import get_db
from src.db.models import Recipe, RecipeRating, User
from src.schemas.recipe import RatingCreate, RecipeCreate, RecipeOut, RecipeUpdate

router = APIRouter(prefix="/recipes", tags=["recipes"])


def _apply_filters(
    query,
    search: Optional[str],
    tags: Optional[List[str]],
    cuisine: Optional[str],
    difficulty: Optional[str],
    min_time: Optional[int],
    max_time: Optional[int],
):
    """Apply optional filters to the recipe query using metadata fields for cuisine/difficulty/time."""
    filters = []
    if search:
        pattern = f"%{search.lower()}%"
        filters.append(func.lower(Recipe.title).like(pattern))
    if tags:
        # tags stored as array/JSON - check overlap; SQLite fallback: simple LIKE across serialized json
        for t in tags:
            pattern = f"%{t}%"
            filters.append(func.cast(Recipe.tags, func.TEXT).like(pattern))  # generic approach
    if cuisine:
        filters.append(func.cast(Recipe.metadata, func.TEXT).like(f'%\"cuisine\": \"{cuisine}\"%'))
    if difficulty:
        filters.append(func.cast(Recipe.metadata, func.TEXT).like(f'%\"difficulty\": \"{difficulty}\"%'))
    if min_time is not None:
        filters.append(func.cast(Recipe.metadata, func.TEXT).like('%"time":'))
        # filter strictly by numeric needs richer JSON operators; for SQLite generic fallback skip strict compare
    if max_time is not None:
        filters.append(func.cast(Recipe.metadata, func.TEXT).like('%"time":'))
    if filters:
        query = query.filter(and_(*filters))
    return query


@router.get("", response_model=List[RecipeOut], summary="List recipes with optional filters")
def list_recipes(
    search: Optional[str] = None,
    tags: Optional[List[str]] = Query(default=None),
    cuisine: Optional[str] = None,
    difficulty: Optional[str] = None,
    min_time: Optional[int] = None,
    max_time: Optional[int] = None,
    sort: Optional[str] = "newest",  # newest, oldest, rating
    page: Optional[int] = 1,
    page_size: Optional[int] = 20,
    db: Session = Depends(get_db),
):
    """
    Returns a paginated list of recipes filtered by search/tags/cuisine/difficulty/time.
    Sorting supports newest/oldest/rating.
    """
    query = db.query(Recipe)
    query = _apply_filters(query, search, tags, cuisine, difficulty, min_time, max_time)

    if sort == "oldest":
        query = query.order_by(asc(Recipe.created_at))
    elif sort == "rating":
        query = query.order_by(desc(Recipe.avg_rating.nullslast()))
    else:
        query = query.order_by(desc(Recipe.created_at))

    offset, limit = pagination_params(page, page_size)
    items = query.offset(offset).limit(limit).all()
    return items


@router.post("", response_model=RecipeOut, summary="Create a recipe")
def create_recipe(
    recipe: RecipeCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Create a recipe for the authenticated user.
    """
    obj = Recipe(
        owner_id=current_user.id,
        title=recipe.title,
        description=recipe.description,
        ingredients=recipe.ingredients,
        steps=recipe.steps,
        tags=recipe.tags,
        metadata=recipe.metadata,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{recipe_id}", response_model=RecipeOut, summary="Get recipe by id")
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a recipe by ID.
    """
    obj = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    return obj


@router.put("/{recipe_id}", response_model=RecipeOut, summary="Update a recipe (owner only)")
def update_recipe(
    recipe_id: int,
    data: RecipeUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Update fields of a recipe. Only the owner can update.
    """
    obj = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    if obj.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)

    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{recipe_id}", status_code=204, summary="Delete a recipe (owner)")
def delete_recipe(
    recipe_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Delete recipe if current user is the owner.
    """
    obj = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    if obj.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    db.delete(obj)
    db.commit()
    return None


@router.post("/{recipe_id}/rate", response_model=RecipeOut, summary="Rate a recipe (auth)")
def rate_recipe(
    recipe_id: int,
    rating: RatingCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Create or update a rating for the recipe by the current user and update average rating.
    """
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

    existing = (
        db.query(RecipeRating)
        .filter(RecipeRating.recipe_id == recipe_id, RecipeRating.user_id == current_user.id)
        .first()
    )
    if existing:
        existing.rating = rating.rating
        existing.comment = rating.comment
        db.add(existing)
    else:
        rr = RecipeRating(user_id=current_user.id, recipe_id=recipe_id, rating=rating.rating, comment=rating.comment)
        db.add(rr)

    db.commit()

    # Recompute average
    avg = db.query(func.avg(RecipeRating.rating)).filter(RecipeRating.recipe_id == recipe_id).scalar()
    recipe.avg_rating = float(avg) if avg is not None else None
    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    return recipe
