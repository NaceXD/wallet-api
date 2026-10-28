"""Auth эндпоинты"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas import Token, UserRegister, UserResponse
from app.services.rate_limiter import login_limiter
from app.services.security import create_access_token, verify_password
from app.services.user_service import create_user, get_user_by_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserRegister, session: Annotated[AsyncSession, Depends(get_session)]):
    """Регистрация нового пользователя"""
    # Проверяем есть ли пользователь с таким email в бд
    existing_user = await get_user_by_email(session=session, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Данный email уже зарегистрирован"
        )
    new_user = await create_user(session=session, user_in=user_in)
    return new_user


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Аутентификация и выдача JWT токена"""
    if request.client:
        client_ip = request.client.host
    else:
        client_ip = "unknown"
    if not login_limiter.is_allowed(f"ip:{client_ip}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Слишком много запросов",
            headers={"Retry-After": str(login_limiter.get_retry_after(f"ip:{client_ip}"))},
        )
    if not login_limiter.is_allowed(f"email:{form_data.username}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Слишком много запросов",
            headers={
                "Retry-After": str(login_limiter.get_retry_after(f"email:{form_data.username}"))
            },
        )
    user = await get_user_by_email(email=form_data.username, session=session)
    if user is None or not verify_password(
        plain_password=form_data.password, hashed_password=user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Не верный email или пароль"
        )
    access_token = create_access_token(subject=str(user.id))
    return {"access_token": access_token, "token_type": "bearer"}
