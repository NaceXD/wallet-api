"""Rate Limter"""

import time
from collections import defaultdict

from app.config import settings


class InMemoryRateLimiter:
    """Хранит историю попыток по ключу в памяти."""

    def __init__(self, max_attempts: int, window_seconds: int):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._attempts: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        """Проверяет лимит. Если можно - записывает текущую попытку и возвращает True"""
        now = time.time()
        self._attempts[key] = [t for t in self._attempts[key] if t > now - self.window_seconds]
        if len(self._attempts[key]) >= self.max_attempts:
            return False
        self._attempts[key].append(now)
        return True

    def get_retry_after(self, key: str) -> int:
        """Сколько секунд осталось до сброса окна"""
        if not self._attempts[key]:
            return 0
        oldest = min(self._attempts[key])
        elapsed = time.time() - oldest
        retry_after = self.window_seconds - elapsed
        return max(0, int(retry_after))


login_limiter = InMemoryRateLimiter(
    max_attempts=settings.LOGIN_RATE_LIMIT,
    window_seconds=settings.LOGIN_RATE_WINDOW_SEC,
)
