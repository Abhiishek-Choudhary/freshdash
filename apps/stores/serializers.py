import math

from rest_framework import serializers

from apps.catalog.models import Product
from apps.stores.models import Store


class StoreSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    distance_km = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()

    class Meta:
        model = Store
        fields = (
            "id",
            "name",
            "image_url",
            "rating",
            "review_count",
            "delivery_time_min",
            "delivery_time_max",
            "delivery_fee",
            "distance_km",
            "categories",
            "is_open",
        )

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return f"https://picsum.photos/seed/{obj.id}/400/300"

    def get_distance_km(self, obj):
        return round(getattr(obj, "distance_km", 0) or 0, 2)

    def get_categories(self, obj):
        return list(
            Product.objects.filter(store=obj, is_deleted=False)
            .values_list("category", flat=True)
            .distinct()
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["id"] = str(data["id"])
        data["deliveryTimeMin"] = data.pop("delivery_time_min")
        data["deliveryTimeMax"] = data.pop("delivery_time_max")
        data["deliveryFee"] = float(data.pop("delivery_fee"))
        data["reviewCount"] = data.pop("review_count")
        data["imageUrl"] = data.pop("image_url")
        data["distanceKm"] = data.pop("distance_km")
        data["isOpen"] = data.pop("is_open")
        return data


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371
    p1, p2 = math.radians(float(lat1)), math.radians(float(lat2))
    dp = math.radians(float(lat2) - float(lat1))
    dl = math.radians(float(lon2) - float(lon1))
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
