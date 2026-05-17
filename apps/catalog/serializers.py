from rest_framework import serializers

from apps.catalog.models import Product


class ProductSerializer(serializers.ModelSerializer):
    store_id = serializers.UUIDField(source="store.id", read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "store_id",
            "name",
            "brand",
            "description",
            "image_url",
            "price",
            "original_price",
            "unit",
            "category",
            "badge",
            "in_stock",
            "stock_count",
            "tags",
            "nutrition",
            "price_per_kg",
        )

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return f"https://picsum.photos/seed/{obj.id}/400/400"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["id"] = str(data["id"])
        data["storeId"] = str(data.pop("store_id"))
        data["imageUrl"] = data.pop("image_url")
        data["originalPrice"] = float(data.pop("original_price")) if data.get("original_price") else None
        data["inStock"] = data.pop("in_stock")
        data["stockCount"] = data.pop("stock_count")
        if data.get("price_per_kg") is not None:
            data["pricePerKg"] = float(data.pop("price_per_kg"))
        else:
            data.pop("price_per_kg", None)
        data["price"] = float(data["price"])
        return data


class VendorProductSerializer(ProductSerializer):
    sku = serializers.CharField()
    low_stock_threshold = serializers.IntegerField()

    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + ("sku", "low_stock_threshold")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["lowStockThreshold"] = data.pop("low_stock_threshold", instance.low_stock_threshold)
        return data


class VendorInventorySerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    is_low_stock = serializers.SerializerMethodField()
    is_sold_out = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "category",
            "unit",
            "price",
            "image_url",
            "stock_count",
            "low_stock_threshold",
            "in_stock",
            "is_low_stock",
            "is_sold_out",
        )

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return f"https://picsum.photos/seed/{obj.id}/200/200"

    def get_is_low_stock(self, obj):
        return obj.is_low_stock

    def get_is_sold_out(self, obj):
        return obj.is_sold_out

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["id"] = str(data["id"])
        data["imageUrl"] = data.pop("image_url")
        data["stockCount"] = data.pop("stock_count")
        data["lowStockThreshold"] = data.pop("low_stock_threshold")
        data["inStock"] = data.pop("in_stock")
        data["isLowStock"] = data.pop("is_low_stock")
        data["isSoldOut"] = data.pop("is_sold_out")
        data["price"] = float(data["price"])
        return data
