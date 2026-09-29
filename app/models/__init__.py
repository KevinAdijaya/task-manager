import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy import Enum as SQLEnum
from sqlmodel import Field, Relationship, SQLModel


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class Priority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


def _enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    """Persist enum .value (e.g. 'done') instead of .name (e.g. 'DONE')."""
    return [member.value for member in enum_cls]


# Shared enum column types — keep name/native_enum in sync with Alembic migration
task_status_col = SQLEnum(
    TaskStatus,
    name="taskstatus",
    native_enum=False,
    values_callable=_enum_values,
)
priority_col = SQLEnum(
    Priority,
    name="priority",
    native_enum=False,
    values_callable=_enum_values,
)


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(Uuid(), primary_key=True, nullable=False),
    )
    email: str = Field(sa_column=Column(String(255), unique=True, index=True, nullable=False))
    username: str = Field(sa_column=Column(String(50), unique=True, index=True, nullable=False))
    hashed_password: str = Field(sa_column=Column(String(255), nullable=False))
    is_active: bool = Field(default=True, sa_column=Column(Boolean, nullable=False, default=True))
    is_superuser: bool = Field(
        default=False, sa_column=Column(Boolean, nullable=False, default=False)
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
    )

    tasks: list["Task"] = Relationship(back_populates="owner")


class Task(SQLModel, table=True):
    __tablename__ = "tasks"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(Uuid(), primary_key=True, nullable=False),
    )
    title: str = Field(sa_column=Column(String(200), nullable=False))
    description: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        sa_column=Column(
            task_status_col,
            nullable=False,
            default=TaskStatus.PENDING,
        ),
    )
    priority: Priority = Field(
        default=Priority.MEDIUM,
        sa_column=Column(
            priority_col,
            nullable=False,
            default=Priority.MEDIUM,
        ),
    )
    category: str | None = Field(default=None, sa_column=Column(String(50), nullable=True))
    due_date: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )

    owner_id: uuid.UUID = Field(
        sa_column=Column(
            Uuid(),
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
    )

    owner: User = Relationship(back_populates="tasks")
