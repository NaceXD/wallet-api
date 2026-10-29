"""Фикстуры для тестов"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings
from app.database import get_session
from app.main import app
from app.models import Base
from app.services.rate_limiter import login_limiter

TEST_DB_URL = settings.database_url.set(database="wallet_test_db")

SERVICE_DB_URL = settings.database_url.set(database="postgres")


@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Создает тестовую БД перед всеми тестами и удаляет после."""
    engine_service = create_async_engine(SERVICE_DB_URL, isolation_level="AUTOCOMMIT")

    async with engine_service.connect() as conn:
        await conn.execute(text("DROP DATABASE IF EXISTS wallet_test_db WITH (FORCE)"))
        await conn.execute(text("CREATE DATABASE wallet_test_db"))

    await engine_service.dispose()

    engine_test = create_async_engine(TEST_DB_URL)

    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await engine_test.dispose()

    yield

    engine_service = create_async_engine(SERVICE_DB_URL, isolation_level="AUTOCOMMIT")
    async with engine_service.connect() as conn:
        await conn.execute(text("DROP DATABASE IF EXISTS wallet_test_db WITH (FORCE)"))

    await engine_service.dispose()


@pytest.fixture
async def client(setup_test_db):
    """Тестовый HTTP-клиент с подменой БД"""
    engine = create_async_engine(TEST_DB_URL, poolclass=NullPool)

    test_session_factory = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)

    async def override_get_session():
        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE wallets, users RESTART IDENTITY CASCADE"))

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Очищаем историю попыток логина перед каждым тестом"""
    login_limiter._attempts.clear()
