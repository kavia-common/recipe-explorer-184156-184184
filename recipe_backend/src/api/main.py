from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.db import run_create_all  # lightweight bootstrap to create tables

app = FastAPI(
    title="Recipe Explorer Backend",
    description="Server-side API for managing users, recipes, and ratings.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
