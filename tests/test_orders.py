import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.accounts.models import UserRole, VendorProfile
from apps.catalog.models import Product
from apps.orders.models import Address, Order, OrderStatus
from apps.orders.services.status import transition_order
from apps.stores.models import Store

User = get_user_model()


@pytest.fixture
def vendor_setup(db):
    user = User.objects.create_user(phone="+911111111111", password="test123", name="V", role=UserRole.VENDOR, email="v@v.com")
    profile = VendorProfile.objects.create(user=user, business_name="Test Store")
    store = Store.objects.create(owner=profile, name="Test", latitude=28.61, longitude=77.20)
    return user, store


@pytest.fixture
def customer(db):
    return User.objects.create_user(phone="+912222222222", password="test123", name="C", role=UserRole.USER, email="c@c.com")


@pytest.mark.django_db
def test_order_status_transition(vendor_setup, customer):
    user, store = vendor_setup
    product = Product.objects.create(store=store, sku="t1", name="Item", category="G", price=100, stock_count=10)
    address = Address.objects.create(user=customer, label="Home", line1="123 St", city="Delhi", state="DL", zip_code="110001")
    order = Order.objects.create(
        display_id="FD-TEST1",
        customer=customer,
        store=store,
        status=OrderStatus.PENDING,
        address_snapshot={"line1": "123"},
        payment_method="cod",
        subtotal=100,
        delivery_fee=0,
        taxes=5,
        discount=0,
        total=105,
    )
    transition_order(order, OrderStatus.CONFIRMED, user)
    order.refresh_from_db()
    assert order.status == OrderStatus.CONFIRMED


@pytest.mark.django_db
def test_nearby_stores_public():
    client = APIClient()
    response = client.get("/api/stores/nearby", {"lat": "28.61", "lng": "77.20"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
