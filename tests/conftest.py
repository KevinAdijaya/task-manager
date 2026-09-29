import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, get_password_hash
from app.database import Base, get_async_session
from app.main import app
from app.models import Priority, Task, TaskStatus, User

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_session():
    """Fresh in-memory database for each test."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_async_session] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpassword123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_user_token(test_user: User) -> str:
    return create_access_token(subject=test_user.id)


@pytest_asyncio.fixture
async def auth_headers(test_user_token: str) -> dict:
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest_asyncio.fixture
async def test_task(db_session: AsyncSession, test_user: User) -> Task:
    task = Task(
        title="Test Task",
        description="Test Description",
        status=TaskStatus.PENDING,
        priority=Priority.MEDIUM,
        category="Test",
        owner_id=test_user.id,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    return task


@pytest_asyncio.fixture
async def multiple_tasks(db_session: AsyncSession, test_user: User) -> list[Task]:
    statuses = [TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.DONE]
    priorities = [Priority.LOW, Priority.MEDIUM, Priority.HIGH]
    categories = ["Work", "Personal"]

    tasks = [
        Task(
            title=f"Task {i}",
            description=f"Description {i}",
            status=statuses[i % 3],
            priority=priorities[i % 3],
            category=categories[i % 2],
            owner_id=test_user.id,
        )
        for i in range(1, 11)
    ]
    db_session.add_all(tasks)
    await db_session.commit()
    for task in tasks:
        await db_session.refresh(task)
    return tasks
