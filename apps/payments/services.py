import logging
import uuid

from django.conf import settings

from apps.orders.models import Order, PaymentMethod, PaymentStatus
from apps.payments.models import Payment, PaymentProvider

logger = logging.getLogger(__name__)


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
        # Public key so the frontend Razorpay Checkout can boot without a
        # separate config call. Never expose RAZORPAY_KEY_SECRET here.
        "publicKey": getattr(settings, "RAZORPAY_KEY_ID", "") if provider == PaymentProvider.RAZORPAY else "",
        "customerName": getattr(order.customer, "name", ""),
        "customerEmail": getattr(order.customer, "email", "") or "",
        "customerPhone": getattr(order.customer, "phone", "") or "",
        "orderDisplayId": order.display_id,
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
        logger.exception("Stripe intent creation failed for payment %s", payment.id)
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
        logger.exception("Razorpay order creation failed for payment %s", payment.id)
        return None


def verify_razorpay_webhook_signature(body: bytes, signature: str, secret: str) -> bool:
    """Verify the X-Razorpay-Signature header against the raw body using the
    webhook secret. Prefers the razorpay SDK if available, falls back to a
    manual HMAC-SHA256 check (Razorpay's algorithm) if the SDK is missing so
    the endpoint still functions."""
    if not signature or not secret:
        return False
    try:
        import razorpay

        client = razorpay.Client(auth=(getattr(settings, "RAZORPAY_KEY_ID", "") or "x", secret))
        client.utility.verify_webhook_signature(
            body.decode("utf-8"), signature, secret
        )
        return True
    except Exception:
        # Manual verification so the endpoint still works if the SDK isn't
        # installed. Razorpay uses HMAC-SHA256 hex digest.
        try:
            import hashlib
            import hmac

            expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
            return hmac.compare_digest(expected, signature)
        except Exception:
            logger.exception("Razorpay webhook signature verification failed unexpectedly")
            return False


def verify_razorpay_payment_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """Verify Razorpay's checkout callback signature (razorpay_signature) using
    the key secret. Called from PaymentConfirmView when the client forwards it."""
    key_secret = getattr(settings, "RAZORPAY_KEY_SECRET", "")
    if not (order_id and payment_id and signature and key_secret):
        return False
    try:
        import razorpay

        client = razorpay.Client(auth=(getattr(settings, "RAZORPAY_KEY_ID", ""), key_secret))
        client.utility.verify_payment_signature(
            {
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature,
            }
        )
        return True
    except Exception:
        try:
            import hashlib
            import hmac

            payload = f"{order_id}|{payment_id}".encode("utf-8")
            expected = hmac.new(key_secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
            return hmac.compare_digest(expected, signature)
        except Exception:
            logger.exception("Razorpay payment signature verification failed unexpectedly")
            return False


def mark_payment_paid(payment: Payment):
    payment.status = PaymentStatus.PAID
    payment.save(update_fields=["status", "updated_at"])
    order = payment.order
    order.payment_status = PaymentStatus.PAID
    order.save(update_fields=["payment_status", "updated_at"])
    # Ledger: buyer is charged the total.
    record_order_charge(order)


# ---------------------------------------------------------------------------
# Ledger helpers — money movement per role at each lifecycle event
# ---------------------------------------------------------------------------

from decimal import Decimal
from apps.payments.models import LedgerEntry, LedgerReason


def _write(user, amount, reason, order=None, description=""):
    if user is None or amount == 0:
        return
    LedgerEntry.objects.create(
        user=user,
        amount=Decimal(str(amount)),
        reason=reason,
        order=order,
        description=description,
    )


def record_order_charge(order: Order):
    """Buyer paid — debit the buyer's ledger. Called from mark_payment_paid
    for prepaid orders, and manually for COD at delivery time."""
    if LedgerEntry.objects.filter(order=order, reason=LedgerReason.ORDER_CHARGE).exists():
        return
    _write(
        order.customer,
        -order.total,
        LedgerReason.ORDER_CHARGE,
        order,
        f"Payment for order {order.display_id}",
    )


def record_order_refund(order: Order):
    """Cancel path — credit the buyer back."""
    if LedgerEntry.objects.filter(order=order, reason=LedgerReason.ORDER_REFUND).exists():
        return
    _write(
        order.customer,
        order.total,
        LedgerReason.ORDER_REFUND,
        order,
        f"Refund for order {order.display_id}",
    )


def record_delivery_earnings(assignment):
    """Delivered → credit the delivery partner."""
    if LedgerEntry.objects.filter(order=assignment.order, reason=LedgerReason.DELIVERY_EARNING).exists():
        return
    user = getattr(assignment.partner, "user", None) if assignment.partner else None
    _write(
        user,
        assignment.driver_earnings,
        LedgerReason.DELIVERY_EARNING,
        assignment.order,
        f"Delivery of {assignment.order.display_id}",
    )


def record_seller_payout(order: Order):
    """Delivered → seller receives the subtotal (product revenue)."""
    if LedgerEntry.objects.filter(order=order, reason=LedgerReason.SELLER_PAYOUT).exists():
        return
    profile = getattr(order.store, "owner", None)
    user = getattr(profile, "user", None) if profile else None
    _write(
        user,
        order.subtotal - order.discount,
        LedgerReason.SELLER_PAYOUT,
        order,
        f"Payout for order {order.display_id}",
    )


def wallet_snapshot(user):
    entries = LedgerEntry.objects.filter(user=user).order_by("-created_at")[:50]
    total = LedgerEntry.objects.filter(user=user).aggregate(
        s=models.Sum("amount")
    )["s"] or Decimal("0")
    return {
        "balance": float(total),
        "entries": [
            {
                "id": str(e.id),
                "amount": float(e.amount),
                "reason": e.reason,
                "description": e.description,
                "orderId": str(e.order_id) if e.order_id else None,
                "createdAt": e.created_at.isoformat(),
            }
            for e in entries
        ],
    }


# Local import so the module-level import at the top isn't polluted
from django.db import models  # noqa: E402
