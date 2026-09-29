from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Task, TaskStatus, User
from app.schemas import TaskCreate, TaskFilterParams, TaskStats, TaskUpdate


class TaskService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, task_in: TaskCreate, owner_id: UUID) -> Task:
        task = Task(
            **task_in.model_dump(),
            owner_id=owner_id,
        )
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def get_by_id(self, task_id: UUID, owner_id: UUID) -> Task | None:
        result = await self.session.execute(
            select(Task)
            .where(Task.id == task_id, Task.owner_id == owner_id)
            .options(selectinload(Task.owner))
        )
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        owner_id: UUID,
        filters: TaskFilterParams,
    ) -> tuple[list[Task], int]:
        query = select(Task).where(Task.owner_id == owner_id)

        if filters.status:
            query = query.where(Task.status == filters.status)
        if filters.priority:
            query = query.where(Task.priority == filters.priority)
        if filters.category:
            query = query.where(Task.category.ilike(f"%{filters.category}%"))
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.where(
                or_(
                    Task.title.ilike(search_term),
                    Task.description.ilike(search_term),
                )
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query) or 0

        # Apply pagination
        query = query.order_by(Task.created_at.desc())
        query = query.offset((filters.page - 1) * filters.page_size).limit(filters.page_size)

        result = await self.session.execute(query)
        tasks = result.scalars().all()

        return list(tasks), total

    async def update(self, task_id: UUID, owner_id: UUID, task_in: TaskUpdate) -> Task | None:
        task = await self.get_by_id(task_id, owner_id)
        if not task:
            return None

        update_data = task_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)

        task.updated_at = datetime.now(UTC)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def delete(self, task_id: UUID, owner_id: UUID) -> bool:
        task = await self.get_by_id(task_id, owner_id)
        if not task:
            return False

        await self.session.delete(task)
        await self.session.commit()
        return True

    async def get_stats(self, owner_id: UUID) -> TaskStats:
        # Total
        total_result = await self.session.execute(
            select(func.count(Task.id)).where(Task.owner_id == owner_id)
        )
        total = total_result.scalar() or 0

        # By status
        status_result = await self.session.execute(
            select(Task.status, func.count(Task.id))
            .where(Task.owner_id == owner_id)
            .group_by(Task.status)
        )
        by_status = {status.value: count for status, count in status_result.all()}

        # By priority
        priority_result = await self.session.execute(
            select(Task.priority, func.count(Task.id))
            .where(Task.owner_id == owner_id)
            .group_by(Task.priority)
        )
        by_priority = {priority.value: count for priority, count in priority_result.all()}

        # Overdue
        overdue_result = await self.session.execute(
            select(func.count(Task.id)).where(
                Task.owner_id == owner_id,
                Task.due_date < datetime.now(UTC),
                Task.status != TaskStatus.DONE,
            )
        )
        overdue = overdue_result.scalar() or 0

        return TaskStats(
            total=total,
            by_status=by_status,
            by_priority=by_priority,
            overdue=overdue,
        )


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self.session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create(self, email: str, username: str, hashed_password: str) -> User:
        user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update(self, user_id: UUID, **kwargs) -> User | None:
        user = await self.get_by_id(user_id)
        if not user:
            return None

        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)

        await self.session.commit()
        await self.session.refresh(user)
        return user
