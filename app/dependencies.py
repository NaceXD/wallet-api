"""FastAPI зависимости"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import User
from app.services.exceptions import InvalidTokenError, TokenIsExpiredError
from app.services.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    session: Annotated[AsyncSession, Depends(get_session)],
    token: str = Depends(oauth2_scheme),
) -> User:
    """Достает текущего пользователя из токена"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token=token)
        user_id = payload.get("sub")
    except (InvalidTokenError, TokenIsExpiredError) as err:
        raise credentials_exception from err

    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user
