import uuid

from django.conf import settings

from apps.orders.models import Order, PaymentMethod, PaymentStatus
from apps.payments.models import Payment, PaymentProvider


def create_payment_intent(order: Order, provider: str | None = None):
    provider = provider or getattr(settings, "PAYMENT_PROVIDER", PaymentProvider.MOCK)
    if order.payment_method == PaymentMethod.COD:
        order.payment_status = PaymentStatus.PENDING
        order.save(update_fields=["payment_status", "updated_at"])
        return {
            "paymentRequired": False,
            "paymentMethod": order.payment_method,
            "orderId": str(order.id),
        }

    payment = Payment.objects.create(
        order=order,
        amount=order.total,
        provider=provider,
        external_id=f"{provider}_{uuid.uuid4().hex[:12]}",
        status=PaymentStatus.PENDING,
        metadata={"displayId": order.display_id},
    )
    client_secret = None
    if provider == PaymentProvider.STRIPE and getattr(settings, "STRIPE_SECRET_KEY", ""):
        client_secret = _stripe_client_secret(payment)
    elif provider == PaymentProvider.RAZORPAY and getattr(settings, "RAZORPAY_KEY_ID", ""):
        client_secret = _razorpay_order_id(payment)

    if not client_secret:
        client_secret = f"mock_secret_{payment.external_id}"

    return {
        "paymentRequired": True,
        "paymentId": str(payment.id),
        "provider": provider,
        "amount": float(payment.amount),
        "currency": payment.currency,
        "clientSecret": client_secret,
        "orderId": str(order.id),
    }


def _stripe_client_secret(payment: Payment) -> str | None:
    try:
        import stripe

        stripe.api_key = settings.STRIPE_SECRET_KEY
        intent = stripe.PaymentIntent.create(
            amount=int(payment.amount * 100),
            currency=payment.currency.lower(),
            metadata={"order_id": str(payment.order_id), "payment_id": str(payment.id)},
        )
        payment.external_id = intent.id
        payment.save(update_fields=["external_id", "updated_at"])
        return intent.client_secret
    except Exception:
        return None


def _razorpay_order_id(payment: Payment) -> str | None:
    try:
        import razorpay

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        rp_order = client.order.create(
            {
                "amount": int(payment.amount * 100),
                "currency": payment.currency,
                "receipt": str(payment.order.display_id),
            }
        )
        payment.external_id = rp_order["id"]
        payment.save(update_fields=["external_id", "updated_at"])
        return rp_order["id"]
    except Exception:
        return None


def mark_payment_paid(payment: Payment):
    payment.status = PaymentStatus.PAID
    payment.save(update_fields=["status", "updated_at"])
    order = payment.order
    order.payment_status = PaymentStatus.PAID
    order.save(update_fields=["payment_status", "updated_at"])
