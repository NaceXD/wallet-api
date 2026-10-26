"""База данных и фабрика сессий"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# Асинхроный движок
engine = create_async_engine(
    settings.database_url,
    echo=settings.APP_DEBUG,
    pool_pre_ping=True,
)

# Фабрика сессии
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


# Зависимости
async def get_session() -> AsyncGenerator[AsyncSession]:
    """Выдает сессию БД для запроса и закрывает её после."""
    async with async_session_factory() as session:
        yield session
