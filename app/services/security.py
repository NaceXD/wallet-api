"""Хэширование пароля и JWT утилиты"""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from app.config import settings
from app.services.exceptions import InvalidTokenError, TokenIsExpiredError

password_hash = PasswordHash.recommended()


def get_password_hash(password: str) -> str:
    """Хэширует пароль"""
    return password_hash.hash(password=password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Верификация пароля"""
    return password_hash.verify(password=plain_password, hash=hashed_password)


def create_access_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    """Создает JWT токен"""
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.JWT_EXPIRES_MIN)

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "iat": datetime.now(UTC),
    }

    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET.get_secret_value(), algorithm=settings.JWT_ALG
    )
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any]:
    """Декодирует JWT, проверяет его подпись/срок действия"""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET.get_secret_value(), algorithms=[settings.JWT_ALG]
        )
        return payload
    except jwt.ExpiredSignatureError as err:
        raise TokenIsExpiredError("Срок действия токена истёк") from err
    except jwt.InvalidTokenError as err:
        raise InvalidTokenError("Ошибка обработки токена") from err
