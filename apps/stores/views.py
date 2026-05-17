from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsVendorOrStaff
from apps.accounts.utils import get_user_store
from apps.stores.models import Store
from apps.stores.serializers import StoreSerializer, haversine_km


class NearbyStoresView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        lat = request.query_params.get("lat", 28.6139)
        lng = request.query_params.get("lng", 77.2090)
        stores = Store.objects.filter(is_active=True)
        annotated = []
        for store in stores:
            store.distance_km = haversine_km(lat, lng, store.latitude, store.longitude)
            annotated.append(store)
        annotated.sort(key=lambda s: s.distance_km)
        return Response(StoreSerializer(annotated, many=True, context={"request": request}).data)


class StoreDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, store_id):
        store = Store.objects.filter(id=store_id, is_active=True).first()
        if not store:
            return Response({"message": "Store not found", "code": "not_found"}, status=404)
        return Response(StoreSerializer(store, context={"request": request}).data)


class StoreOpenToggleView(APIView):
    permission_classes = [IsAuthenticated, IsVendorOrStaff]

    def patch(self, request):
        store = get_user_store(request.user)
        if not store:
            return Response({"message": "No store linked", "code": "no_store"}, status=400)
        is_open = request.data.get("isOpen", request.data.get("is_open"))
        if is_open is None:
            return Response({"message": "isOpen required", "code": "validation_error"}, status=400)
        store.is_open = bool(is_open)
        store.save(update_fields=["is_open", "updated_at"])
        return Response(StoreSerializer(store, context={"request": request}).data)
