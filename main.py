from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from database import engine


app = FastAPI(
    title="AI Project Mentor API",
    description=(
        "FastAPI backend for managing projects, tasks "
        "and AI mentor interactions."
    ),
    version="1.0.0",
)


@app.get("/", tags=["General"])
def root():
    return {
        "message": "Welcome to AI Project Mentor API",
        "documentation": "/docs",
    }


@app.get("/api/health", tags=["Health"])
def health_check():
    try:
        with engine.connect() as connection:
            database_name = connection.execute(
                text("SELECT DB_NAME()")
            ).scalar()

        return {
            "status": "healthy",
            "backend": "connected",
            "database": "connected",
            "database_name": database_name,
        }

    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=503,
            detail="Backend is running, but SQL Server is unavailable.",
        ) from error