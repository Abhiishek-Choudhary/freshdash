from django.contrib import admin

from apps.catalog.models import Product, ProductRelation


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "store", "sku", "stock_count", "in_stock")
    list_filter = ("store", "category")


admin.site.register(ProductRelation)
