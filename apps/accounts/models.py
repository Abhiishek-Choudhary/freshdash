import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from apps.accounts.managers import UserManager


class UserRole(models.TextChoices):
    USER = "user", "Customer"
    VENDOR = "vendor", "Vendor"
    STAFF = "staff", "Store Staff"
    DELIVERY_PARTNER = "delivery_partner", "Delivery Partner"
    ADMIN = "admin", "Admin"


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(max_length=20, unique=True, db_index=True)
    email = models.EmailField(max_length=255, unique=True, null=True, blank=True)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=32, choices=UserRole.choices, default=UserRole.USER)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    expo_push_token = models.CharField(max_length=255, blank=True, default="")
    device_platform = models.CharField(max_length=16, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        db_table = "users"

    def __str__(self):
        return f"{self.name} ({self.phone})"

    def save(self, *args, **kwargs):
        if self.role == UserRole.ADMIN:
            self.is_staff = True
        super().save(*args, **kwargs)


class VendorProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="vendor_profile")
    business_name = models.CharField(max_length=255, blank=True)
    gstin = models.CharField(max_length=32, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "vendor_profiles"


class DeliveryPartnerProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="delivery_profile"
    )
    is_online = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=4.8)
    vehicle_type = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "delivery_partner_profiles"


class OtpPurpose(models.TextChoices):
    LOGIN = "login", "Login"
    SIGNUP = "signup", "Signup"
    RESET_PASSWORD = "reset_password", "Reset Password"


class OtpChallenge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(max_length=20, db_index=True)
    code_hash = models.CharField(max_length=128)
    purpose = models.CharField(max_length=32, choices=OtpPurpose.choices)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    consumed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "otp_challenges"
        indexes = [models.Index(fields=["phone", "purpose", "consumed"])]
