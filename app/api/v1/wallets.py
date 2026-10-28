"""Wallet эндпоинты"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.dependencies import get_current_user
from app.models import User
from app.schemas import OperationRequest, OperationResponse, WalletCreateResponse, WalletResponse
from app.services.wallet_service import apply_operation, create_wallet, get_wallet

router = APIRouter(prefix="/wallets", tags=["wallets"])


@router.post("", response_model=WalletCreateResponse, status_code=status.HTTP_201_CREATED)
async def wallet_create(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Создает новый кошелек для текущего пользователя."""
    return await create_wallet(session=session, user_id=current_user.id)


@router.get("/{wallet_id}", response_model=WalletResponse, status_code=status.HTTP_200_OK)
async def wallet_get(
    wallet_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Возвращает баланс кошелька. Доступен только владельцу."""
    return await get_wallet(session=session, wallet_id=wallet_id, user_id=current_user.id)


@router.post(
    "/{wallet_id}/operation", response_model=OperationResponse, status_code=status.HTTP_200_OK
)
async def wallet_operation(
    wallet_id: UUID,
    payload: OperationRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Применяет Deposit или Withdraw к кошельку"""
    new_balance = await apply_operation(
        session=session,
        user_id=current_user.id,
        wallet_id=wallet_id,
        operation_type=payload.operation_type,
        amount=payload.amount,
    )
    return {"id": wallet_id, "balance": new_balance}
