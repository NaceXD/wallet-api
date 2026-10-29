import asyncio
from decimal import Decimal

import pytest


async def get_auth_headers(client, email: str) -> dict:
    """Вспомогательная функция: регистрирует пользователя и возвращает заголовки с токеном"""
    await client.post("/api/v1/auth/register", json={"email": email, "password": "testpass123"})
    response = await client.post(
        "/api/v1/auth/login", data={"username": email, "password": "testpass123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def create_test_wallet(client, headers: dict) -> str:
    """Вспомогательная функция: cоздает кошелек и возращает его ID"""
    response = await client.post("/api/v1/wallets", headers=headers)
    assert response.status_code == 201
    return response.json()["id"]


async def create_funded_wallet(
    client, headers: dict, amount: int | float | Decimal = Decimal("100.0")
) -> str:
    """Вспомогательная функция: создает кошелек и сразу пополняет его на нужную сумму"""
    wallet_id = await create_test_wallet(client, headers)

    await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": str(amount)},
        headers=headers,
    )
    return wallet_id


async def test_create_and_get_wallet(client):
    """Создание кошелька и проверка, что баланс 0"""
    headers = await get_auth_headers(client, "wallet1@test.com")

    response = await client.post("/api/v1/wallets", headers=headers)

    assert response.status_code == 201

    data = response.json()
    assert Decimal(data["balance"]) == Decimal("0.00")
    wallet_id = data["id"]

    response = await client.get(f"/api/v1/wallets/{wallet_id}", headers=headers)

    assert response.status_code == 200
    assert Decimal(response.json()["balance"]) == Decimal("0.00")


async def test_deposit_and_withdraw(client):
    """Пополнение и списание средств"""
    headers = await get_auth_headers(client, "wallet2@test.com")

    wallet_id = await create_test_wallet(client, headers)

    deposit_response = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": 150.50},
        headers=headers,
    )

    assert deposit_response.status_code == 200
    assert Decimal(deposit_response.json()["balance"]) == Decimal("150.50")

    withdraw_response = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "WITHDRAW", "amount": 50.50},
        headers=headers,
    )

    assert withdraw_response.status_code == 200
    assert Decimal(withdraw_response.json()["balance"]) == Decimal("100.00")


async def test_withdraw_insufficient_funds(client):
    """Ошибка 400 при попытке списать больше, чем есть"""
    headers = await get_auth_headers(client, "wallet3@test.com")
    wallet_id = await create_funded_wallet(client, headers, amount=100)

    response = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "WITHDRAW", "amount": 200},
        headers=headers,
    )

    assert response.status_code == 400


async def test_access_foreign_wallet(client):
    """Ошибка 404 при попытке доступа к чужому кошельку"""
    headers_user1 = await get_auth_headers(client, "user1@test.com")
    wallet_id_user1 = await create_test_wallet(client, headers_user1)

    headers_user2 = await get_auth_headers(client, "user2@test.com")

    response = await client.get(f"/api/v1/wallets/{wallet_id_user1}", headers=headers_user2)

    assert response.status_code == 404


async def test_concurrent_withdrawals(client):
    """20 паралельных списаний по 10 при балансе 100."""
    headers = await get_auth_headers(client, "race@test.com")

    wallet_id = await create_funded_wallet(client, headers, amount=100)

    async def withdraw():
        return await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "WITHDRAW", "amount": 10},
            headers=headers,
        )

    responses = await asyncio.gather(*[withdraw() for _ in range(20)])

    success_count = sum(1 for r in responses if r.status_code == 200)
    error_count = sum(1 for r in responses if r.status_code == 400)

    assert success_count == 10
    assert error_count == 10

    response = await client.get(f"/api/v1/wallets/{wallet_id}", headers=headers)
    assert Decimal(response.json()["balance"]) == Decimal("0.00")


@pytest.mark.parametrize(
    "operation, amount",
    [
        ("DEPOSIT", 0),
        ("DEPOSIT", -100),
        ("WITHDRAW", -5),
        ("DEPOSIT", 10.001),
        ("DEPOSIT", 1000000000000000000),
        ("TRANSFER", 100),
    ],
)
async def test_operation_invalid_data(client, operation, amount):
    """Pydantic должен вернуть 422 при невалидной сумме или операции"""
    headers = await get_auth_headers(client, "edge_invalid@test.com")
    wallet_id = await create_test_wallet(client, headers)

    response = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": operation, "amount": amount},
        headers=headers,
    )

    assert response.status_code == 422


async def test_withdraw_exact_balance(client):
    """Списание равно всей суммы должно быть валидно, баланс станет 0"""
    headers = await get_auth_headers(client, "edge_exact@test.com")
    wallet_id = await create_funded_wallet(client, headers, amount=100)

    response = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "WITHDRAW", "amount": 100},
        headers=headers,
    )

    assert response.status_code == 200

    response = await client.get(f"/api/v1/wallets/{wallet_id}", headers=headers)
    assert Decimal(response.json()["balance"]) == Decimal("0.00")


async def test_withdraw_one_cent_more_than_balance(client):
    """Списание на 0.01 больше должно вернуть 400"""
    headers = await get_auth_headers(client, "edge_cent@test.com")
    wallet_id = await create_funded_wallet(client, headers, amount=100)

    response = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "WITHDRAW", "amount": 100.01},
        headers=headers,
    )
    assert response.status_code == 400


async def test_invalid_uuid_in_path(client):
    """Если в URL передать не UUID, FastAPI вернет 422"""
    headers = await get_auth_headers(client, "edge_uuid@test.com")

    response = await client.get("/api/v1/wallets/not-a-uuid", headers=headers)
    assert response.status_code == 422
