from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import Priority, TaskStatus


# --- User Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=72)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = Field(
        default=None, min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$"
    )
    is_active: bool | None = None


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
    is_superuser: bool
    created_at: datetime


class UserReadWithTasks(UserRead):
    tasks_count: int = 0


# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: UUID
    exp: int
    type: str


class LoginRequest(BaseModel):
    """Login with email + password (username is not required to sign in)."""

    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# --- Task Schemas ---
class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    status: TaskStatus = TaskStatus.PENDING
    priority: Priority = Priority.MEDIUM
    category: str | None = Field(default=None, max_length=50)
    due_date: datetime | None = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    status: TaskStatus | None = None
    priority: Priority | None = None
    category: str | None = Field(default=None, max_length=50)
    due_date: datetime | None = None


class TaskRead(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID
    created_at: datetime
    updated_at: datetime


class TaskReadWithOwner(TaskRead):
    owner_username: str


# --- Pagination & Filter Schemas ---
class TaskFilterParams(BaseModel):
    status: TaskStatus | None = None
    priority: Priority | None = None
    category: str | None = Field(default=None, max_length=50)
    search: str | None = Field(default=None, max_length=100)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[TaskRead]
    total: int
    page: int
    page_size: int
    total_pages: int


# --- Stats Schema ---
class TaskStats(BaseModel):
    total: int
    by_status: dict[str, int]
    by_priority: dict[str, int]
    overdue: int


# --- Error Schemas ---
class ErrorResponse(BaseModel):
    detail: str


class ValidationErrorResponse(BaseModel):
    detail: list[dict]
