import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from main import app
from src.entity.models import Base, User
from src.database.db import get_db
from src.services.auth import auth_service

# 🔧 Параметри підключення до тестової SQLite бази
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

# 🔐 Дані тестового користувача
test_user = {
    "username": "test_admin",
    "email": "admin@example.com",
    "password": "12345678"
}

@pytest.fixture(autouse=True)
def mock_fastapi_limiter():
    with patch("fastapi_limiter.FastAPILimiter.init", new_callable=AsyncMock), \
            patch("fastapi_limiter.FastAPILimiter.redis", new=AsyncMock()), \
            patch("fastapi_limiter.FastAPILimiter.identifier", new=AsyncMock(return_value="test_identifier")), \
            patch("fastapi_limiter.FastAPILimiter.http_callback", new=AsyncMock(return_value=None)), \
            patch("fastapi_limiter.depends.RateLimiter", new=lambda *args, **kwargs: lambda: True):
        yield

# ✅ Shared AsyncSession для всіх фікстур
@pytest_asyncio.fixture(scope="module")
async def session():
    async with TestingSessionLocal() as session:
        yield session

# ✅ Заміна get_db залежності на фікстуру session
@pytest.fixture(scope="module")
def override_get_db(session):
    async def _override():
        yield session
    return _override

# ✅ Ініціалізація таблиць і створення test_user
@pytest.fixture(scope="module", autouse=True)
def init_models_wrap(session):
    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

        # створення test_user у поточній сесії
        hash_password = auth_service.get_password_hash(test_user["password"])
        current_user = User(
            username=test_user["username"],
            email=test_user["email"],
            password=hash_password,
            confirmed=True
        )
        session.add(current_user)
        await session.commit()

    asyncio.run(init_models())

# ✅ Клієнт з підміною залежності get_db
@pytest.fixture(scope="module")
def client(override_get_db):
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

# ✅ Отримання access токена для test_user
@pytest_asyncio.fixture()
async def get_token():
    token = await auth_service.create_access_token(data={"sub": test_user["email"]})
    return token
