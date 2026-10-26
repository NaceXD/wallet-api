"""Настройки приложения"""

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    APP_ENV: str
    APP_DEBUG: bool

    POSTGRES_USER: str
    POSTGRES_PASSWORD: SecretStr
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    JWT_SECRET: SecretStr
    JWT_ALG: str
    JWT_EXPIRES_MIN: int

    LOGIN_RATE_LIMIT: int
    LOGIN_RATE_WINDOW_SEC: int

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def database_url(self) -> URL:
        """Собирает URL для подключения к БД"""
        return URL.create(
            "postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD.get_secret_value(),
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        )


settings = Settings()
