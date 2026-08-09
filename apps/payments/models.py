import uuid

from django.conf import settings
from django.db import models

from apps.orders.models import Order, PaymentStatus


class PaymentProvider(models.TextChoices):
    RAZORPAY = "razorpay", "Razorpay"
    STRIPE = "stripe", "Stripe"
    MOCK = "mock", "Mock"


class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default="INR")
    provider = models.CharField(max_length=16, choices=PaymentProvider.choices, default=PaymentProvider.MOCK)
    external_id = models.CharField(max_length=128, blank=True, db_index=True)
    status = models.CharField(max_length=16, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payments"
        ordering = ["-created_at"]


class LedgerReason(models.TextChoices):
    ORDER_CHARGE = "order_charge", "Order charge"
    ORDER_REFUND = "order_refund", "Order refund"
    SELLER_PAYOUT = "seller_payout", "Seller payout"
    DELIVERY_EARNING = "delivery_earning", "Delivery earning"
    PLATFORM_FEE = "platform_fee", "Platform fee"
    ADJUSTMENT = "adjustment", "Manual adjustment"


class LedgerEntry(models.Model):
    """Money movement per user. Positive amount = credit, negative = debit.
    Balance is derived by summing amounts."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ledger_entries"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.CharField(max_length=32, choices=LedgerReason.choices)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name="ledger_entries")
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ledger_entries"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "-created_at"])]
