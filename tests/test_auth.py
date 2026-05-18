import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.accounts.models import UserRole

User = get_user_model()


@pytest.mark.django_db
def test_password_login():
    User.objects.create_user(
        phone="+919999999999",
        password="secret123",
        name="Test",
        email="t@t.com",
        role=UserRole.USER,
    )
    client = APIClient()
    response = client.post(
        "/api/auth/login/password",
        {"phone": "+919999999999", "password": "secret123"},
        format="json",
    )
    assert response.status_code == 200
    data = response.json()
    assert "accessToken" in data["tokens"]
    assert data["user"]["phone"] == "+919999999999"


@pytest.mark.django_db
def test_otp_login_flow():
    User.objects.create_user(
        phone="+918888888888",
        password="x",
        name="Otp User",
        email="o@o.com",
        role=UserRole.USER,
    )
    client = APIClient()
    r1 = client.post("/api/auth/login", {"phone": "+918888888888"}, format="json")
    assert r1.status_code == 200
    assert r1.json()["otpSent"] is True
    r2 = client.post(
        "/api/auth/verify-otp",
        {"phone": "+918888888888", "otp": "123456"},
        format="json",
    )
    assert r2.status_code == 200
    assert "tokens" in r2.json()


@pytest.mark.django_db
def test_signup_then_verify_otp():
    client = APIClient()
    phone = "+917777777777"
    r1 = client.post(
        "/api/auth/signup",
        {
            "name": "New User",
            "email": "new@freshdash.demo",
            "phone": phone,
            "role": UserRole.USER,
        },
        format="json",
    )
    assert r1.status_code == 200
    assert r1.json()["otpSent"] is True
    r2 = client.post(
        "/api/auth/verify-otp",
        {"phone": phone, "otp": "123456"},
        format="json",
    )
    assert r2.status_code == 200
    assert r2.json()["user"]["phone"] == phone
