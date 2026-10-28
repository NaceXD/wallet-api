"""Точка входа в FastAPI"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.api.v1.auth import router as auth
from app.api.v1.wallets import router as wallet
from app.services.exceptions import InsufficientFundsError, WalletNotFoundError

app = FastAPI(title="Wallet API", version="0.1.0")


@app.exception_handler(InsufficientFundsError)
async def insufficient_funds_handler(request: Request, exc: InsufficientFundsError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Не достаточно средств для списания"},
    )


@app.exception_handler(WalletNotFoundError)
async def wallet_not_found_handler(request: Request, exc: WalletNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Кошелек не найден"}
    )


app.include_router(auth, prefix="/api/v1")
app.include_router(wallet, prefix="/api/v1")
