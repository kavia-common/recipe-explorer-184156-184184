from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers.auth import router as auth_router
from src.api.routers.recipes import router as recipes_router
from src.core.config import get_settings
from src.db import run_create_all  # lightweight bootstrap to create tables

openapi_tags = [
    {"name": "system", "description": "System and health endpoints"},
    {"name": "auth", "description": "Authentication endpoints"},
    {"name": "recipes", "description": "Recipe management endpoints"},
]

app = FastAPI(
    title="Recipe Explorer Backend",
    description="Server-side API for managing users, recipes, and ratings.",
    version="0.1.0",
    openapi_tags=openapi_tags,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup_bootstrap():
    """
    Create tables if they do not exist. This is a simple bootstrap to avoid
    requiring migrations at this stage. For production, replace with Alembic.
    """
    try:
        run_create_all()
    except Exception as exc:
        # Avoid crashing on startup; log to console in this minimal setup.
        # In production, use a proper logger.
        print(f"[DB Bootstrap] Skipped create_all due to: {exc}")


@app.get("/", summary="Health Check", tags=["system"])
def health_check():
    """
    Health check endpoint.

    Returns:
        JSON body with a simple message.
    """
    return {"message": "Healthy"}


# Register routers
app.include_router(auth_router)
app.include_router(recipes_router)
