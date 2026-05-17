from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsVendorOrStaff
from apps.accounts.utils import get_user_store
from apps.orders.models import Address, Coupon, DeliverySlotConfig, Order, OrderStatus
from apps.orders.serializers import AddressSerializer, serialize_order
from apps.orders.services.create_order import create_order, validate_coupon
from apps.orders.services.restock import restock_order_items
from apps.orders.services.status import transition_order
from apps.delivery.services import create_assignment_for_order


class AddressListCreateView(APIView):
    def get(self, request):
        addresses = Address.objects.filter(user=request.user)
        return Response([AddressSerializer.to_representation(a) for a in addresses])

    def post(self, request):
        fields = AddressSerializer.from_request(request.data)
        if fields.get("is_default"):
            Address.objects.filter(user=request.user).update(is_default=False)
        address = Address.objects.create(user=request.user, **fields)
        return Response(AddressSerializer.to_representation(address), status=201)


class AddressDetailView(APIView):
    def get_object(self, request, address_id):
        return Address.objects.filter(id=address_id, user=request.user).first()

    def put(self, request, address_id):
        address = self.get_object(request, address_id)
        if not address:
            return Response({"message": "Not found", "code": "not_found"}, status=404)
        fields = AddressSerializer.from_request(request.data)
        for k, v in fields.items():
            setattr(address, k, v)
        if fields.get("is_default"):
            Address.objects.filter(user=request.user).exclude(id=address.id).update(is_default=False)
        address.save()
        return Response(AddressSerializer.to_representation(address))

    def delete(self, request, address_id):
        address = self.get_object(request, address_id)
        if not address:
            return Response({"message": "Not found", "code": "not_found"}, status=404)
        address.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrderListCreateView(APIView):
    def get(self, request):
        orders = Order.objects.filter(customer=request.user).select_related("store")
        return Response([serialize_order(o, request) for o in orders])

    def post(self, request):
        if request.user.role not in ("user", "admin"):
            return Response({"message": "Only customers can place orders", "code": "forbidden"}, status=403)
        order = create_order(request.user, request.data)
        return Response(serialize_order(order, request), status=201)


class OrderDetailView(APIView):
    def get(self, request, order_id):
        order = Order.objects.filter(id=order_id).select_related("store").first()
        if not order:
            return Response({"message": "Not found", "code": "not_found"}, status=404)
        if order.customer_id != request.user.id:
            store = get_user_store(request.user)
            if not store or order.store_id != store.id:
                from apps.delivery.models import DeliveryAssignment

                assigned = DeliveryAssignment.objects.filter(
                    order=order, partner__user=request.user
                ).exists()
                if not assigned and request.user.role != "admin":
                    return Response({"message": "Forbidden", "code": "forbidden"}, status=403)
        return Response(serialize_order(order, request))


class OrderTrackView(APIView):
    def get(self, request, order_id):
        order = Order.objects.filter(id=order_id, customer=request.user).first()
        if not order:
            return Response({"message": "Not found", "code": "not_found"}, status=404)
        return Response(
            {
                "status": order.status,
                "estimatedDelivery": order.estimated_delivery_at.isoformat()
                if order.estimated_delivery_at
                else None,
            }
        )


class CheckoutPreviewView(APIView):
    def get(self, request):
        from apps.cart.services import get_or_create_cart, cart_items_response

        cart = get_or_create_cart(request.user)
        items = cart_items_response(cart, request)
        subtotal = sum(
            float(i["product"]["price"]) * i["quantity"] for i in items
        )
        delivery_fee = 29.0
        discount = 0.0
        taxes = (subtotal - discount) * 0.05
        total = subtotal - discount + delivery_fee + taxes
        address = Address.objects.filter(user=request.user, is_default=True).first()
        return Response(
            {
                "items": items,
                "summary": {
                    "itemTotal": subtotal,
                    "deliveryFee": delivery_fee,
                    "taxes": taxes,
                    "discount": discount,
                    "total": total,
                },
                "address": AddressSerializer.to_representation(address) if address else None,
            }
        )


class CheckoutSlotsView(APIView):
    def get(self, request):
        slots = DeliverySlotConfig.objects.all()
        return Response(
            [
                {
                    "id": s.id,
                    "label": s.label,
                    "sublabel": s.sublabel,
                    "isExpress": s.is_express,
                }
                for s in slots
            ]
        )


class CouponValidateView(APIView):
    def post(self, request):
        code = request.data.get("couponCode") or request.data.get("code")
        subtotal = Decimal(str(request.data.get("subtotal", 0)))
        try:
            _, discount = validate_coupon(code, subtotal)
            return Response({"valid": True, "discount": float(discount)})
        except Exception as exc:
            from apps.accounts.exceptions import APIError

            if isinstance(exc, APIError):
                return Response({"valid": False, "discount": 0, "message": exc.detail["message"]})
            return Response({"valid": False, "discount": 0})


class VendorOrderListView(APIView):
    permission_classes = [IsAuthenticated, IsVendorOrStaff]

    def get(self, request):
        store = get_user_store(request.user)
        if not store:
            return Response([])
        orders = Order.objects.filter(store=store).select_related("store")
        return Response([serialize_order(o, request) for o in orders])


class VendorOrderActionView(APIView):
    permission_classes = [IsAuthenticated, IsVendorOrStaff]

    def patch(self, request, order_id, action):
        store = get_user_store(request.user)
        order = Order.objects.filter(id=order_id, store=store).first()
        if not order:
            return Response({"message": "Not found", "code": "not_found"}, status=404)
        if action == "accept":
            transition_order(order, OrderStatus.CONFIRMED, request.user, "Accepted")
        elif action == "prepare":
            transition_order(order, OrderStatus.PREPARING, request.user, "Preparing")
        elif action == "reject":
            transition_order(order, OrderStatus.CANCELLED, request.user, "Rejected by vendor")
            restock_order_items(order)
        elif action == "ready":
            transition_order(order, OrderStatus.READY_FOR_PICKUP, request.user, "Ready for pickup")
            create_assignment_for_order(order)
        return Response(serialize_order(order, request))


class VendorDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsVendorOrStaff]

    def get(self, request):
        from django.utils.timesince import timesince

        from apps.catalog.models import Product

        store = get_user_store(request.user)
        if not store:
            return Response({"message": "No store", "code": "no_store"}, status=400)
        today = timezone.now().date()
        today_orders = Order.objects.filter(store=store, created_at__date=today).exclude(
            status=OrderStatus.CANCELLED
        )
        revenue = today_orders.aggregate(total=Sum("total"))["total"] or 0
        active = Order.objects.filter(
            store=store,
            status__in=[
                OrderStatus.PENDING,
                OrderStatus.CONFIRMED,
                OrderStatus.PREPARING,
            ],
        ).count()
        in_delivery = Order.objects.filter(
            store=store,
            status__in=[OrderStatus.OUT_FOR_DELIVERY, OrderStatus.READY_FOR_PICKUP],
        ).count()
        recent = Order.objects.filter(store=store).order_by("-created_at")[:5]
        recent_data = []
        status_map = {
            OrderStatus.PENDING: ("new", "New Order"),
            OrderStatus.CONFIRMED: ("new", "Confirmed"),
            OrderStatus.PREPARING: ("preparing", "Preparing"),
            OrderStatus.OUT_FOR_DELIVERY: ("on_way", "On the way"),
            OrderStatus.READY_FOR_PICKUP: ("preparing", "Ready"),
        }
        for o in recent:
            st, label = status_map.get(o.status, ("new", o.status))
            recent_data.append(
                {
                    "id": o.display_id,
                    "itemCount": o.items.count(),
                    "total": float(o.total),
                    "timeAgo": timesince(o.created_at),
                    "status": st,
                    "statusLabel": label,
                }
            )
        from django.db import models as db_models

        low_stock = list(
            Product.objects.filter(store=store, is_deleted=False)
            .filter(stock_count__lte=db_models.F("low_stock_threshold"))
            .values("id", "name", "stock_count")[:5]
        )
        return Response(
            {
                "todayRevenue": float(revenue),
                "revenueChange": 12.5,
                "activeOrders": active,
                "inDelivery": in_delivery,
                "recentOrders": recent_data,
                "inventoryAlerts": low_stock,
            }
        )


class VendorAnalyticsView(APIView):
    permission_classes = [IsAuthenticated, IsVendorOrStaff]

    def get(self, request):
        store = get_user_store(request.user)
        week_ago = timezone.now() - timezone.timedelta(days=7)
        orders = Order.objects.filter(store=store, created_at__gte=week_ago).exclude(
            status=OrderStatus.CANCELLED
        )
        revenue = orders.aggregate(total=Sum("total"))["total"] or 0
        count = orders.count()
        delivered = orders.filter(status=OrderStatus.DELIVERED).count()
        return Response(
            {
                "weeklyRevenue": float(revenue),
                "averageOrderValue": float(revenue / count) if count else 0,
                "fulfillmentRate": (delivered / count * 100) if count else 0,
                "orderCount": count,
            }
        )
