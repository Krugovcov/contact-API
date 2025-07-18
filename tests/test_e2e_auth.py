from unittest.mock import Mock

import pytest
from sqlalchemy import select
from src.entity.models import User
from src.conf import messages
from tests.conftest import TestingSessionLocal

user_data = {"username": "test_user", "email": "test@example.com", "password": "12345678"}

def test_signup(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    response = client.post("api/auth/signup", json=user_data)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "password" not in data
    assert "avatar" in data

def repeat_signup(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    response = client.post("api/auth/signup", json=user_data)
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == messages.ACCOUNT_EXIST

def test_not_confirmed_login(client):
    response = client.post("api/auth/login", data={"username": user_data["email"], "password": user_data["password"]})
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == messages.NOT_CONFIRMED

@pytest.mark.asyncio
async def test_login(client):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(select(User).where(User.email == user_data["email"]))
        current_user = current_user.scalar_one_or_none()
        if current_user:
            current_user.confirmed = True
            await session.commit()
    response = client.post("api/auth/login", data={"username": user_data["email"], "password": user_data["password"]})
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"

def test_wrong_password_login(client):
    response = client.post("api/auth/login", data={"username": user_data["email"], "password": "wrongpassword"})
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == messages.INVALID_PASSWORD

def test_wrong_email_login(client):
    response = client.post("api/auth/login", data={"username": "incorectemail", "password": user_data["password"]})
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == messages.INVALID_EMAIL

def test_validation_eror_login(client):
    response = client.post("api/auth/login", data={"password": user_data["password"]})
    assert response.status_code == 422, response.text
    data = response.json()
    assert "detail" in data