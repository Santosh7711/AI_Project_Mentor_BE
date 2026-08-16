from fastapi import Depends, FastAPI, HTTPException, Response, status
from sqlalchemy import case, func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from datetime import datetime

from database import engine, get_db
from models import Project, Task
from schemas import (
    DashboardResponse,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    TaskCreate,
    TaskResponse,
    TaskStatusUpdate,
    TaskUpdate,
)


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


# ---------------------------------------------------------
# Task endpoints
# ---------------------------------------------------------

@app.post(
    "/api/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Tasks"],
)
def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
):
    project = db.get(Project, task_data.project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Project with ID {task_data.project_id} "
                "was not found."
            ),
        )

    new_task = Task(
        project_id=task_data.project_id,
        title=task_data.title,
        description=task_data.description,
        priority=task_data.priority,
        status=task_data.status,
        ai_generated=task_data.ai_generated,
    )

    try:
        db.add(new_task)
        db.commit()
        db.refresh(new_task)

        return new_task

    except SQLAlchemyError as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Task could not be created.",
        ) from error


@app.get(
    "/api/tasks",
    response_model=list[TaskResponse],
    tags=["Tasks"],
)
def get_tasks(
    db: Session = Depends(get_db),
):
    statement = select(Task).order_by(Task.task_id)

    tasks = db.scalars(statement).all()

    return tasks


@app.get(
    "/api/tasks/{task_id}",
    response_model=TaskResponse,
    tags=["Tasks"],
)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
):
    task = db.get(Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} was not found.",
        )

    return task


@app.put(
    "/api/tasks/{task_id}",
    response_model=TaskResponse,
    tags=["Tasks"],
)
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
):
    task = db.get(Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} was not found.",
        )

    project = db.get(Project, task_data.project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Project with ID {task_data.project_id} "
                "was not found."
            ),
        )

    task.project_id = task_data.project_id
    task.title = task_data.title
    task.description = task_data.description
    task.priority = task_data.priority
    task.status = task_data.status
    task.ai_generated = task_data.ai_generated
    task.updated_at = datetime.now()

    try:
        db.commit()
        db.refresh(task)

        return task

    except SQLAlchemyError as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Task could not be updated.",
        ) from error


@app.patch(
    "/api/tasks/{task_id}/status",
    response_model=TaskResponse,
    tags=["Tasks"],
)
def update_task_status(
    task_id: int,
    status_data: TaskStatusUpdate,
    db: Session = Depends(get_db),
):
    task = db.get(Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} was not found.",
        )

    task.status = status_data.status
    task.updated_at = datetime.now()

    try:
        db.commit()
        db.refresh(task)

        return task

    except SQLAlchemyError as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Task status could not be updated.",
        ) from error


@app.delete(
    "/api/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Tasks"],
)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
):
    task = db.get(Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} was not found.",
        )

    try:
        db.delete(task)
        db.commit()

        return Response(
            status_code=status.HTTP_204_NO_CONTENT
        )

    except SQLAlchemyError as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Task could not be deleted.",
        ) from error


# ---------------------------------------------------------
# Dashboard endpoint
# ---------------------------------------------------------

@app.get(
    "/api/dashboard",
    response_model=DashboardResponse,
    tags=["Dashboard"],
)
def get_dashboard(
    db: Session = Depends(get_db),
):
    try:
        total_projects = db.scalar(
            select(func.count(Project.project_id))
        ) or 0

        total_tasks = db.scalar(
            select(func.count(Task.task_id))
        ) or 0

        pending_tasks = db.scalar(
            select(func.count(Task.task_id)).where(
                Task.status == "Pending"
            )
        ) or 0

        in_progress_tasks = db.scalar(
            select(func.count(Task.task_id)).where(
                Task.status == "In Progress"
            )
        ) or 0

        completed_tasks = db.scalar(
            select(func.count(Task.task_id)).where(
                Task.status == "Completed"
            )
        ) or 0

        progress_statement = (
            select(
                Project.project_id,
                Project.project_name,
                Project.technology_stack,
                func.count(Task.task_id).label("total_tasks"),
                func.sum(
                    case(
                        (Task.status == "Completed", 1),
                        else_=0,
                    )
                ).label("completed_tasks"),
            )
            .outerjoin(
                Task,
                Project.project_id == Task.project_id,
            )
            .group_by(
                Project.project_id,
                Project.project_name,
                Project.technology_stack,
            )
            .order_by(Project.project_id)
        )

        progress_rows = db.execute(
            progress_statement
        ).all()

        project_progress = []

        for row in progress_rows:
            project_total = row.total_tasks or 0
            project_completed = row.completed_tasks or 0

            if project_total == 0:
                progress_percentage = 0.0

            else:
                progress_percentage = round(
                    (project_completed / project_total) * 100,
                    2,
                )

            project_progress.append(
                {
                    "project_id": row.project_id,
                    "project_name": row.project_name,
                    "technology_stack": row.technology_stack,
                    "total_tasks": project_total,
                    "completed_tasks": project_completed,
                    "progress_percentage": progress_percentage,
                }
            )

        recent_tasks_statement = (
            select(
                Task.task_id,
                Task.title,
                Task.project_id,
                Project.project_name,
                Task.priority,
                Task.status,
                Task.updated_at,
                Task.created_at,
            )
            .join(
                Project,
                Task.project_id == Project.project_id,
            )
            .order_by(
                func.coalesce(
                    Task.updated_at,
                    Task.created_at,
                ).desc()
            )
            .limit(5)
        )

        recent_task_rows = db.execute(
            recent_tasks_statement
        ).all()

        recent_tasks = []

        for row in recent_task_rows:
            recent_tasks.append(
                {
                    "task_id": row.task_id,
                    "title": row.title,
                    "project_id": row.project_id,
                    "project_name": row.project_name,
                    "priority": row.priority,
                    "status": row.status,
                    "updated_at": (
                        row.updated_at or row.created_at
                    ),
                }
            )

        return {
            "total_projects": total_projects,
            "total_tasks": total_tasks,
            "pending_tasks": pending_tasks,
            "in_progress_tasks": in_progress_tasks,
            "completed_tasks": completed_tasks,
            "project_progress": project_progress,
            "recent_tasks": recent_tasks,
        }

    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Dashboard data could not be retrieved.",
        ) from error