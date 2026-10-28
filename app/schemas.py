"""Pydantic схемы"""

from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# --- Схемы для работы с пользователем и токеном ---
class UserRegister(BaseModel):
    """Схема создания нового пользователя"""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class UserResponse(BaseModel):
    """Схема ответа"""

    id: UUID
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """Схема ответа токена"""

    access_token: str
    token_type: str = "bearer"  # noqa: S105
    model_config = ConfigDict(from_attributes=True)


# --- Схемы для работы с кошельком ---


class OperationType(StrEnum):
    """Тип операции с кошельком"""

    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class OperationRequest(BaseModel):
    """Запрос на операцию."""

    operation_type: OperationType
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)


class OperationResponse(BaseModel):
    """Схема возвращение баланса после операции"""

    id: UUID
    balance: Decimal

    model_config = ConfigDict(from_attributes=True)


class WalletResponse(BaseModel):
    """Информация о кошельке."""

    id: UUID
    balance: Decimal
    user_id: UUID

    model_config = ConfigDict(from_attributes=True)


class WalletCreateResponse(WalletResponse):
    """Ответ на создание кошелька"""
