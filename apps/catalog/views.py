from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsVendorOrStaff
from apps.accounts.utils import get_user_store
from apps.catalog.models import Product, ProductRelation
from apps.catalog.serializers import ProductSerializer, VendorInventorySerializer, VendorProductSerializer
from apps.stores.models import Store


class StoreProductsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, store_id):
        qs = Product.objects.filter(store_id=store_id, is_deleted=False, in_stock=True)
        category = request.query_params.get("category")
        if category:
            qs = qs.filter(category__icontains=category)
        return Response(ProductSerializer(qs, many=True, context={"request": request}).data)


class ProductDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, product_id):
        product = Product.objects.filter(id=product_id, is_deleted=False).first()
        if not product:
            return Response({"message": "Product not found", "code": "not_found"}, status=404)
        return Response(ProductSerializer(product, context={"request": request}).data)


class ProductSearchView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        q = request.query_params.get("q", "")
        category = request.query_params.get("category")
        qs = Product.objects.filter(is_deleted=False, in_stock=True)
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(brand__icontains=q) | Q(category__icontains=q))
        if category:
            qs = qs.filter(category__icontains=category)
        return Response(ProductSerializer(qs[:50], many=True, context={"request": request}).data)


class ProductScanView(APIView):
    permission_classes = [AllowAny]

    def _lookup(self, request, barcode: str):
        product = Product.objects.filter(barcode=barcode, is_deleted=False).first()
        if not product:
            return Response({"message": "Product not found", "code": "not_found"}, status=404)
        return Response(ProductSerializer(product, context={"request": request}).data)

    def get(self, request):
        barcode = request.query_params.get("barcode")
        if not barcode:
            return Response({"message": "barcode required", "code": "validation_error"}, status=400)
        return self._lookup(request, barcode)

    def post(self, request):
        from apps.catalog.barcode import decode_barcode_from_image

        barcode = request.data.get("barcode") or request.query_params.get("barcode")
        if not barcode and request.FILES.get("image"):
            barcode = decode_barcode_from_image(request.FILES["image"])
            if not barcode:
                return Response(
                    {
                        "message": "Could not read barcode from image. Install pyzbar or send barcode field.",
                        "code": "barcode_decode_failed",
                    },
                    status=400,
                )
        if not barcode:
            return Response(
                {"message": "barcode or image required", "code": "validation_error"},
                status=400,
            )
        return self._lookup(request, barcode)


class RelatedProductsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, product_id):
        related_ids = ProductRelation.objects.filter(product_id=product_id).values_list(
            "related_product_id", flat=True
        )
        qs = Product.objects.filter(id__in=related_ids, is_deleted=False)
        if not qs.exists():
            product = Product.objects.filter(id=product_id).first()
            if product:
                qs = (
                    Product.objects.filter(store=product.store, category=product.category, is_deleted=False)
                    .exclude(id=product_id)[:6]
                )
        return Response(ProductSerializer(qs, many=True, context={"request": request}).data)


class VendorProductListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsVendorOrStaff]

    def get(self, request):
        store = get_user_store(request.user)
        if not store:
            return Response({"message": "No store", "code": "no_store"}, status=400)
        qs = Product.objects.filter(store=store, is_deleted=False)
        return Response(VendorInventorySerializer(qs, many=True, context={"request": request}).data)

    def post(self, request):
        store = get_user_store(request.user)
        if not store:
            return Response({"message": "No store", "code": "no_store"}, status=400)
        data = request.data.copy()
        sku = data.get("sku") or f"SKU-{Product.objects.filter(store=store).count() + 1}"
        product = Product.objects.create(
            store=store,
            sku=sku,
            name=data.get("name", "New Product"),
            brand=data.get("brand", ""),
            description=data.get("description", ""),
            price=data.get("price", 0),
            original_price=data.get("originalPrice") or data.get("original_price"),
            unit=data.get("unit", "pc"),
            category=data.get("category", "General"),
            badge=data.get("badge"),
            stock_count=int(data.get("stockCount") or data.get("stock_count") or 0),
            low_stock_threshold=int(
                data.get("lowStockThreshold") or data.get("low_stock_threshold") or 5
            ),
            in_stock=bool(data.get("inStock", data.get("in_stock", True))),
            tags=data.get("tags", []),
            nutrition=data.get("nutrition"),
            barcode=data.get("barcode"),
        )
        if request.FILES.get("image"):
            product.image = request.FILES["image"]
            product.save()
        return Response(VendorProductSerializer(product, context={"request": request}).data, status=201)


class VendorProductDetailView(APIView):
    permission_classes = [IsAuthenticated, IsVendorOrStaff]

    def get_object(self, request, product_id):
        store = get_user_store(request.user)
        return Product.objects.filter(id=product_id, store=store, is_deleted=False).first()

    def put(self, request, product_id):
        product = self.get_object(request, product_id)
        if not product:
            return Response({"message": "Not found", "code": "not_found"}, status=404)
        for field, keys in [
            ("name", ["name"]),
            ("brand", ["brand"]),
            ("description", ["description"]),
            ("price", ["price"]),
            ("unit", ["unit"]),
            ("category", ["category"]),
            ("badge", ["badge"]),
            ("barcode", ["barcode"]),
        ]:
            for key in keys:
                if key in request.data:
                    setattr(product, field, request.data[key])
        if "originalPrice" in request.data or "original_price" in request.data:
            product.original_price = request.data.get("originalPrice") or request.data.get("original_price")
        if "stockCount" in request.data or "stock_count" in request.data:
            product.stock_count = int(request.data.get("stockCount") or request.data.get("stock_count"))
        if "lowStockThreshold" in request.data or "low_stock_threshold" in request.data:
            product.low_stock_threshold = int(
                request.data.get("lowStockThreshold") or request.data.get("low_stock_threshold")
            )
        if "inStock" in request.data or "in_stock" in request.data:
            product.in_stock = bool(request.data.get("inStock", request.data.get("in_stock")))
        if request.FILES.get("image"):
            product.image = request.FILES["image"]
        product.save()
        return Response(VendorProductSerializer(product, context={"request": request}).data)

    def delete(self, request, product_id):
        product = self.get_object(request, product_id)
        if not product:
            return Response({"message": "Not found", "code": "not_found"}, status=404)
        product.is_deleted = True
        product.save(update_fields=["is_deleted"])
        return Response(status=status.HTTP_204_NO_CONTENT)
