"""Кастомные ошибки"""


class InvalidTokenError(ValueError):
    """Вызывается при других ошибках токена"""


class TokenIsExpiredError(ValueError):
    """Вызывается когда срок действия токена истек"""
