import pytest


async def test_register_user(client):
    """Проверяем успешную регистрацию пользователя."""
    response = await client.post(
        "/api/v1/auth/register", json={"email": "test@example.com", "password": "test12345"}
    )

    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"


async def test_register_duplicate_email(client):
    """Ошибка при попытке зарегистрировать уже существующий email"""
    await client.post(
        "/api/v1/auth/register", json={"email": "dup@example.com", "password": "test12345"}
    )

    response = await client.post(
        "/api/v1/auth/register", json={"email": "dup@example.com", "password": "test123456"}
    )

    assert response.status_code == 400


async def test_login_success(client):
    """Успешная авторизация, получение токина"""
    await client.post(
        "/api/v1/auth/register", json={"email": "validuser@example.com", "password": "validpass123"}
    )
    response = await client.post(
        "/api/v1/auth/login", data={"username": "validuser@example.com", "password": "validpass123"}
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"  # noqa: S105


async def test_login_wrong_password(client):
    """Ошибка при неверном пароле"""
    await client.post(
        "/api/v1/auth/register", json={"email": "valid@example.com", "password": "validpass123"}
    )

    response = await client.post(
        "/api/v1/auth/login", data={"username": "valid@example.com", "password": "invalidpass123"}
    )

    assert response.status_code == 401


async def test_login_noexistent_email(client):
    """Ошибка при попытке входа с несуществующим email"""
    response = await client.post(
        "/api/v1/auth/login", data={"username": "invalid@example.com", "password": "testpass12312"}
    )

    assert response.status_code == 401


async def test_login_rate_limit(client):
    """Проверка блокировки после 5 неудачных попыток"""
    await client.post(
        "/api/v1/auth/register", json={"email": "test@example.com", "password": "testpass123"}
    )

    for _ in range(5):
        await client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com", "password": "invalidpass123"},
        )

    response = await client.post(
        "/api/v1/auth/login", data={"username": "test@example.com", "password": "testpass123"}
    )

    assert response.status_code == 429

    assert "Retry-After" in response.headers
    assert response.headers["Retry-After"].isdigit()


@pytest.mark.parametrize(
    "email, password",
    [
        ("not-an-email", "validpass123"),
        ("user@test.com", "s1234"),
        ("user@test.com", "a" * 129),
        ("", "validpass12345"),
    ],
)
async def test_register_invalid_data(client, email, password):
    """Pydantic должен вернуть 422 при невалидных данных"""
    response = await client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )

    assert response.status_code == 422
