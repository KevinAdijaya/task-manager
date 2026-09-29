from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_session, get_current_active_user
from app.models import User
from app.schemas import (
    PaginatedResponse,
    TaskCreate,
    TaskFilterParams,
    TaskRead,
    TaskStats,
    TaskUpdate,
)
from app.services import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_in: TaskCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    service = TaskService(session)
    task = await service.create(task_in, current_user.id)
    return task


@router.get("/", response_model=PaginatedResponse)
async def list_tasks(
    status: str | None = Query(None, description="Filter by status"),
    priority: str | None = Query(None, description="Filter by priority"),
    category: str | None = Query(None, description="Filter by category"),
    search: str | None = Query(None, description="Search in title and description"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    from app.models import Priority, TaskStatus

    filters = TaskFilterParams(
        status=TaskStatus(status) if status else None,
        priority=Priority(priority) if priority else None,
        category=category,
        search=search,
        page=page,
        page_size=page_size,
    )

    service = TaskService(session)
    tasks, total = await service.get_multi(current_user.id, filters)

    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        items=tasks,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/stats/summary", response_model=TaskStats)
async def get_task_stats(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    service = TaskService(session)
    stats = await service.get_stats(current_user.id)
    return stats


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
    task_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    service = TaskService(session)
    task = await service.get_by_id(task_id, current_user.id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return task


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: UUID,
    task_in: TaskUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    service = TaskService(session)
    task = await service.update(task_id, current_user.id, task_in)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    service = TaskService(session)
    deleted = await service.delete(task_id, current_user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
