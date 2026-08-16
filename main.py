from fastapi import Depends, FastAPI, HTTPException, Response, status
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from database import engine, get_db
from models import Project
from schemas import ProjectCreate, ProjectResponse, ProjectUpdate


app = FastAPI(
    title="AI Project Mentor API",
    description=(
        "FastAPI backend for managing projects, tasks "
        "and AI mentor interactions."
    ),
    version="1.0.0",
)


# ---------------------------------------------------------
# General endpoints
# ---------------------------------------------------------

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
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Backend is running, but SQL Server is unavailable.",
        ) from error


# ---------------------------------------------------------
# Project endpoints
# ---------------------------------------------------------

@app.post(
    "/api/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Projects"],
)
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
):
    new_project = Project(
        project_name=project_data.project_name,
        description=project_data.description,
        technology_stack=project_data.technology_stack,
    )

    try:
        db.add(new_project)
        db.commit()
        db.refresh(new_project)

        return new_project

    except SQLAlchemyError as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Project could not be created.",
        ) from error


@app.get(
    "/api/projects",
    response_model=list[ProjectResponse],
    tags=["Projects"],
)
def get_projects(
    db: Session = Depends(get_db),
):
    statement = select(Project).order_by(Project.project_id)

    projects = db.scalars(statement).all()

    return projects


@app.get(
    "/api/projects/{project_id}",
    response_model=ProjectResponse,
    tags=["Projects"],
)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} was not found.",
        )

    return project


@app.put(
    "/api/projects/{project_id}",
    response_model=ProjectResponse,
    tags=["Projects"],
)
def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} was not found.",
        )

    project.project_name = project_data.project_name
    project.description = project_data.description
    project.technology_stack = project_data.technology_stack

    try:
        db.commit()
        db.refresh(project)

        return project

    except SQLAlchemyError as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Project could not be updated.",
        ) from error


@app.delete(
    "/api/projects/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Projects"],
)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} was not found.",
        )

    try:
        db.delete(project)
        db.commit()

        return Response(
            status_code=status.HTTP_204_NO_CONTENT
        )

    except SQLAlchemyError as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Project could not be deleted.",
        ) from error