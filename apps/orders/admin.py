from django.contrib import admin

from apps.orders.models import Address, Coupon, DeliverySlotConfig, Order, OrderItem, OrderStatusLog


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("display_id", "customer", "store", "status", "total", "created_at")
    list_filter = ("status",)


admin.site.register(Address)
admin.site.register(Coupon)
admin.site.register(DeliverySlotConfig)
admin.site.register(OrderItem)
admin.site.register(OrderStatusLog)
