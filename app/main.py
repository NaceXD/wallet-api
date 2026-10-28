"""Точка входа в FastAPI"""

from fastapi import FastAPI

from app.api.v1.auth import router as auth

app = FastAPI(title="Wallet API", version="0.1.0")

app.include_router(auth, prefix="/api/v1")
