from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.models import DeliveryPartnerProfile, OtpChallenge, User, VendorProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("phone", "name", "role", "is_active")
    list_filter = ("role", "is_active")
    search_fields = ("phone", "name", "email")
    ordering = ("phone",)
    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        ("Personal", {"fields": ("name", "email", "role", "avatar")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {"fields": ("phone", "name", "email", "role", "password1", "password2")}),
    )


admin.site.register(VendorProfile)
admin.site.register(DeliveryPartnerProfile)
admin.site.register(OtpChallenge)
