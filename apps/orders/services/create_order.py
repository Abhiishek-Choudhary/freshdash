import random
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.accounts.exceptions import APIError
from apps.catalog.models import Product
from apps.orders.models import Address, Coupon, Order, OrderItem, OrderStatus, OrderStatusLog
from apps.stores.models import Store


def generate_display_id():
    num = random.randint(1000, 9999)
    return f"FD-{num}"


def address_to_snapshot(address: Address) -> dict:
    return {
        "id": str(address.id),
        "label": address.label,
        "line1": address.line1,
        "line2": address.line2,
        "city": address.city,
        "state": address.state,
        "zipCode": address.zip_code,
        "isDefault": address.is_default,
    }


def validate_coupon(code: str, subtotal: Decimal) -> tuple[Coupon | None, Decimal]:
    if not code:
        return None, Decimal("0")
    coupon = Coupon.objects.filter(code__iexact=code, is_active=True).first()
    if not coupon:
        raise APIError("Invalid coupon", code="invalid_coupon")
    now = timezone.now()
    if not (coupon.valid_from <= now <= coupon.valid_to):
        raise APIError("Coupon expired", code="coupon_expired")
    if subtotal < coupon.min_order:
        raise APIError("Order below minimum for coupon", code="coupon_min_not_met")
    if coupon.discount_type == "percent":
        discount = subtotal * coupon.value / Decimal("100")
        if coupon.max_discount:
            discount = min(discount, coupon.max_discount)
    else:
        discount = coupon.value
    return coupon, discount


@transaction.atomic
def create_order(user, data):
    store_id = data.get("storeId") or data.get("store_id")
    items = data.get("items", [])
    address_id = data.get("addressId") or data.get("address_id")
    payment_method = data.get("paymentMethod") or data.get("payment_method", "cod")
    delivery_slot_id = data.get("deliverySlotId") or data.get("delivery_slot_id", "express")
    coupon_code = data.get("couponCode") or data.get("coupon_code")

    if not items:
        raise APIError("Order items required", code="validation_error")
    if not address_id:
        raise APIError("Address required", code="validation_error")

    address = Address.objects.filter(id=address_id, user=user).first()
    if not address:
        raise APIError("Address not found", code="not_found", status_code=404)

    products = []
    for entry in items:
        pid = entry.get("productId") or entry.get("product_id")
        qty = int(entry.get("quantity", 1))
        product = Product.objects.select_for_update().filter(id=pid, is_deleted=False).first()
        if not product:
            raise APIError(f"Product {pid} not found", code="not_found")
        if not store_id:
            store_id = str(product.store_id)
        elif str(product.store_id) != str(store_id):
            raise APIError("All items must be from the same store", code="validation_error")
        if product.stock_count < qty:
            raise APIError(f"Insufficient stock for {product.name}", code="out_of_stock")
        products.append((product, qty))

    store = Store.objects.select_for_update().get(id=store_id)
    if not store.is_open:
        raise APIError("Store is currently closed", code="store_closed")
    if not store.is_active:
        raise APIError("Store unavailable", code="store_inactive")

    subtotal = sum(p.price * qty for p, qty in products)
    delivery_fee = store.delivery_fee
    coupon, discount = validate_coupon(coupon_code, subtotal) if coupon_code else (None, Decimal("0"))
    taxable = subtotal - discount
    taxes = taxable * Decimal(str(settings.TAX_RATE))
    total = taxable + delivery_fee + taxes

    display_id = generate_display_id()
    while Order.objects.filter(display_id=display_id).exists():
        display_id = generate_display_id()

    eta_at = timezone.now() + timedelta(minutes=store.delivery_time_max)
    order = Order.objects.create(
        display_id=display_id,
        customer=user,
        store=store,
        status=OrderStatus.PENDING,
        address_snapshot=address_to_snapshot(address),
        delivery_slot_id=delivery_slot_id,
        delivery_slot_label=delivery_slot_id.replace("_", " ").title(),
        payment_method=payment_method,
        coupon=coupon,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        taxes=taxes,
        discount=discount,
        total=total,
        estimated_delivery_at=eta_at,
    )

    for product, qty in products:
        image_url = ""
        if product.image:
            image_url = product.image.url
        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            unit=product.unit,
            unit_price=product.price,
            quantity=qty,
            line_total=product.price * qty,
            image_url=image_url,
        )
        product.stock_count -= qty
        if product.stock_count == 0:
            product.in_stock = False
        product.save(update_fields=["stock_count", "in_stock", "updated_at"])

    OrderStatusLog.objects.create(
        order=order, from_status="", to_status=OrderStatus.PENDING, changed_by=user, note="Order placed"
    )
    return order
