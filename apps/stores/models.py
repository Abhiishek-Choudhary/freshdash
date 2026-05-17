import uuid

from django.conf import settings
from django.db import models

from apps.accounts.models import VendorProfile


class Store(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(VendorProfile, on_delete=models.CASCADE, related_name="stores")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="stores/", null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, default=28.6139)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, default=77.2090)
    delivery_time_min = models.PositiveIntegerField(default=15)
    delivery_time_max = models.PositiveIntegerField(default=25)
    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=4.5)
    review_count = models.PositiveIntegerField(default=0)
    is_open = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "stores"

    def __str__(self):
        return self.name


class StoreStaff(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="store_staff")
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="staff")
    can_manage_inventory = models.BooleanField(default=True)
    can_manage_orders = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "store_staff"
        unique_together = ("user", "store")


class StoreHours(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="hours")
    weekday = models.PositiveSmallIntegerField()  # 0=Monday
    open_time = models.TimeField()
    close_time = models.TimeField()
    is_closed = models.BooleanField(default=False)

    class Meta:
        db_table = "store_hours"
        unique_together = ("store", "weekday")
