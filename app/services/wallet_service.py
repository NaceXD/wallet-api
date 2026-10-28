"""Бизнес-логика работы с кошельками"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Wallet
from app.schemas import OperationType
from app.services.exceptions import InsufficientFundsError, WalletNotFoundError


async def create_wallet(session: AsyncSession, user_id: UUID) -> Wallet:
    """Создаёт новый кошелек с нулевым балансом."""
    wallet = Wallet(user_id=user_id)
    session.add(wallet)
    await session.commit()
    await session.refresh(wallet)
    return wallet


async def get_wallet(session: AsyncSession, user_id: UUID, wallet_id: UUID) -> Wallet:
    """Получаем кошелек, проверяя, что он принадлежит пользователю"""
    query = select(Wallet).where(Wallet.id == wallet_id, Wallet.user_id == user_id)
    result = await session.execute(query)
    wallet = result.scalar_one_or_none()

    if wallet is None:
        raise WalletNotFoundError

    return wallet


async def apply_operation(
    session: AsyncSession,
    wallet_id: UUID,
    user_id: UUID,
    operation_type: OperationType,
    amount: Decimal,
) -> Decimal:
    """Атомарно применяет операцию к балансу кошелька. Возвращает новый баланс"""
    if operation_type == OperationType.DEPOSIT:
        stmt = (
            update(Wallet)
            .where(Wallet.id == wallet_id, Wallet.user_id == user_id)
            .values(balance=Wallet.balance + amount)
            .returning(Wallet.balance)
        )
    else:
        stmt = (
            update(Wallet)
            .where(
                Wallet.id == wallet_id,
                Wallet.user_id == user_id,
                Wallet.balance >= amount,
            )
            .values(balance=Wallet.balance - amount)
            .returning(Wallet.balance)
        )

    result = await session.execute(stmt)
    row = result.first()

    if row is None:
        exists = await session.scalar(
            select(Wallet.id).where(Wallet.id == wallet_id, Wallet.user_id == user_id)
        )
        if exists is None:
            raise WalletNotFoundError
        else:
            raise InsufficientFundsError

    await session.commit()

    return row.balance
