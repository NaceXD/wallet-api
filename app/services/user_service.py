from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.schemas import UserRegister
from app.services.security import get_password_hash


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """Ищет пользователя по email"""
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_user(session: AsyncSession, user_in: UserRegister) -> User:
    """Создаем нового пользователя и хэшурем пароль"""
    hash_password = get_password_hash(password=user_in.password)
    user = User(email=user_in.email, hashed_password=hash_password)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
