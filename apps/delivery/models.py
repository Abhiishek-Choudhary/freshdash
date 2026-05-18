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
