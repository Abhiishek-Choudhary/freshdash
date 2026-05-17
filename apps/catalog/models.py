import uuid

from django.db import models

from apps.stores.models import Store


class ProductBadge(models.TextChoices):
    ORGANIC = "ORGANIC", "Organic"
    SALE = "SALE", "Sale"


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="products")
    sku = models.CharField(max_length=64)
    barcode = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    name = models.CharField(max_length=255)
    brand = models.CharField(max_length=128, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="products/", null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    unit = models.CharField(max_length=32, default="pc")
    category = models.CharField(max_length=128, db_index=True)
    badge = models.CharField(max_length=16, choices=ProductBadge.choices, null=True, blank=True)
    stock_count = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    in_stock = models.BooleanField(default=True)
    tags = models.JSONField(default=list, blank=True)
    nutrition = models.JSONField(null=True, blank=True)
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products"
        unique_together = ("store", "sku")
        indexes = [models.Index(fields=["store", "category"])]

    @property
    def is_low_stock(self):
        return 0 < self.stock_count <= self.low_stock_threshold

    @property
    def is_sold_out(self):
        return self.stock_count == 0 or not self.in_stock


class ProductRelation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="related_from")
    related_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="related_to")

    class Meta:
        db_table = "product_relations"
        unique_together = ("product", "related_product")
