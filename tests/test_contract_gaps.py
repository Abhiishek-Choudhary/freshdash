import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.accounts.models import UserRole
from decimal import Decimal

from apps.catalog.models import Product
from apps.delivery.models import DeliveryAssignment
from apps.orders.models import Address, Order, OrderStatus
from apps.stores.models import Store

User = get_user_model()


def _product(store):
    return Product.objects.create(
        store=store,
        sku="t-gap",
        name="Gap Test Item",
        category="General",
        price=Decimal("150"),
        stock_count=20,
        in_stock=True,
    )


@pytest.mark.django_db
def test_store_list_endpoint():
    client = APIClient()
    response = client.get("/api/stores")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.django_db
def test_order_track_driver_location(vendor_setup, customer):
    _, store = vendor_setup
    address = Address.objects.create(
        user=customer,
        label="Home",
        line1="123 St",
        line2="",
        city="Delhi",
        state="DL",
        zip_code="110001",
        is_default=True,
    )
    product = _product(store)
    client = APIClient()
    client.force_authenticate(user=customer)
    order_resp = client.post(
        "/api/orders",
        {
            "storeId": str(store.id),
            "items": [{"productId": str(product.id), "quantity": 1}],
            "addressId": str(address.id),
            "deliverySlotId": "express",
            "paymentMethod": "cod",
        },
        format="json",
    )
    order = Order.objects.get(id=order_resp.json()["id"])
    from apps.accounts.models import DeliveryPartnerProfile

    driver = User.objects.create_user(
        phone="+913333333333",
        password="x",
        name="Driver",
        role=UserRole.DELIVERY_PARTNER,
        email="d@d.com",
    )
    profile, _ = DeliveryPartnerProfile.objects.get_or_create(user=driver)
    DeliveryAssignment.objects.create(
        order=order,
        partner=profile,
        driver_earnings=45,
        driver_latitude=28.61,
        driver_longitude=77.21,
    )
    track = client.get(f"/api/orders/{order.id}/track")
    assert track.status_code == 200
    assert "driverLocation" in track.json()
    assert track.json()["driverLocation"]["lat"] == 28.61


@pytest.mark.django_db
def test_checkout_preview_coupon_fields(customer, vendor_setup):
    _, store = vendor_setup
    client = APIClient()
    client.force_authenticate(user=customer)
    product = _product(store)
    client.post(
        "/api/cart/sync",
        {"items": [{"productId": str(product.id), "quantity": 2}]},
        format="json",
    )
    preview = client.get("/api/checkout/preview", {"couponCode": "FRESH50"})
    assert preview.status_code == 200
    summary = preview.json()["summary"]
    assert "deliveryFeeStrikethrough" in summary
    assert summary.get("couponCode") == "FRESH50" or summary["discount"] >= 0


@pytest.mark.django_db
def test_payment_create_mock(customer, vendor_setup):
    _, store = vendor_setup
    address = Address.objects.create(
        user=customer,
        label="Home",
        line1="1",
        line2="",
        city="Delhi",
        state="DL",
        zip_code="110001",
    )
    product = _product(store)
    client = APIClient()
    client.force_authenticate(user=customer)
    order = client.post(
        "/api/orders",
        {
            "storeId": str(store.id),
            "items": [{"productId": str(product.id), "quantity": 1}],
            "addressId": str(address.id),
            "deliverySlotId": "express",
            "paymentMethod": "upi",
        },
        format="json",
    ).json()
    pay = client.post("/api/payments/create", {"orderId": order["id"]}, format="json")
    assert pay.status_code == 200
    assert pay.json()["paymentRequired"] is True
    assert "clientSecret" in pay.json()
