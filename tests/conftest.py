import pytest
from django.contrib.auth import get_user_model

from apps.accounts.models import UserRole, VendorProfile
from apps.stores.models import Store

User = get_user_model()


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def vendor_setup(db):
    user = User.objects.create_user(
        phone="+911111111111",
        password="test123",
        name="V",
        role=UserRole.VENDOR,
        email="v@v.com",
    )
    profile = VendorProfile.objects.create(user=user, business_name="Test Store")
    store = Store.objects.create(owner=profile, name="Test", latitude=28.61, longitude=77.20)
    return user, store


@pytest.fixture
def customer(db):
    return User.objects.create_user(
        phone="+912222222222",
        password="test123",
        name="C",
        role=UserRole.USER,
        email="c@c.com",
    )
