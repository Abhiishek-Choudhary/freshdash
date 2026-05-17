from django.contrib import admin

from apps.stores.models import Store, StoreHours, StoreStaff


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "is_open", "is_active")


admin.site.register(StoreStaff)
admin.site.register(StoreHours)
