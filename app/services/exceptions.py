"""Кастомные ошибки"""


class InvalidTokenError(ValueError):
    """Вызывается при других ошибках токена"""


class InsufficientFundsError(ValueError):
    """Не достаточно средств для списания."""


class TokenIsExpiredError(ValueError):
    """Вызывается когда срок действия токена истек"""


class WalletNotFoundError(ValueError):
    """Кошелек не найден"""
