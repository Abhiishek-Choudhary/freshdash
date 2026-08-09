import uuid

from django.db import models

from apps.accounts.models import DeliveryPartnerProfile
from apps.orders.models import Order


class DeliveryAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="delivery_assignment")
    partner = models.ForeignKey(
        DeliveryPartnerProfile, on_delete=models.CASCADE, related_name="assignments"
    )
    driver_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    driver_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    driver_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_updated_at = models.DateTimeField(null=True, blank=True)
    pickup_confirmed_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "delivery_assignments"


class BidStatus(models.TextChoices):
    OPEN = "open", "Open"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"
    CANCELLED = "cancelled", "Cancelled"


class DeliveryBid(models.Model):
    """A delivery partner offers to deliver an order for a given amount.
    The seller (or buyer) accepts one, which creates the DeliveryAssignment."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="delivery_bids")
    partner = models.ForeignKey(
        DeliveryPartnerProfile, on_delete=models.CASCADE, related_name="bids"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    eta_minutes = models.PositiveIntegerField(default=30)
    note = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=16, choices=BidStatus.choices, default=BidStatus.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "delivery_bids"
        ordering = ["amount", "created_at"]
        unique_together = ("order", "partner")
        indexes = [models.Index(fields=["order", "status"])]
