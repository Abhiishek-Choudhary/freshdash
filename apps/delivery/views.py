from django.db.models import Sum
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsDeliveryPartner
from apps.delivery.models import DeliveryAssignment
from apps.orders.models import Order, OrderStatus
from apps.orders.serializers import serialize_order
from apps.orders.services.status import transition_order


class DeliveryDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsDeliveryPartner]

    def get(self, request):
        profile = request.user.delivery_profile
        today = timezone.now().date()
        today_assignments = DeliveryAssignment.objects.filter(
            partner=profile, assigned_at__date=today
        )
        earnings = today_assignments.aggregate(total=Sum("driver_earnings"))["total"] or 0
        delivered = today_assignments.filter(delivered_at__isnull=False).count()
        active = DeliveryAssignment.objects.filter(
            partner=profile,
            order__status__in=[OrderStatus.READY_FOR_PICKUP, OrderStatus.OUT_FOR_DELIVERY],
            delivered_at__isnull=True,
        ).select_related("order", "order__customer").first()
        active_data = None
        if active:
            addr = active.order.address_snapshot
            active_data = {
                "id": str(active.id),
                "displayId": active.order.display_id,
                "customerName": active.order.customer.name,
                "itemCount": active.order.items.count(),
                "etaMinutes": 15,
                "addressLine1": addr.get("line1", ""),
                "addressLine2": addr.get("line2", ""),
                "mapImageUrl": "https://picsum.photos/seed/map/800/400",
            }
        return Response(
            {
                "earningsToday": float(earnings),
                "earningsChange": 8.2,
                "deliveriesCount": delivered,
                "completionRate": 98.5,
                "timeOnline": "4h 12m",
                "shiftEndsIn": "2h 48m",
                "activeOrder": active_data,
                "hotspots": [
                    {"id": "h1", "name": "Downtown Hub", "surgeBonus": 50},
                    {"id": "h2", "name": "Green Park", "surgeBonus": 30},
                ],
            }
        )


class PartnerOnlineView(APIView):
    permission_classes = [IsAuthenticated, IsDeliveryPartner]

    def patch(self, request):
        profile = request.user.delivery_profile
        is_online = request.data.get("isOnline", request.data.get("is_online", True))
        profile.is_online = bool(is_online)
        profile.save(update_fields=["is_online"])
        return Response({"isOnline": profile.is_online})


class AssignmentListView(APIView):
    permission_classes = [IsAuthenticated, IsDeliveryPartner]

    def get(self, request):
        qs = DeliveryAssignment.objects.filter(partner=request.user.delivery_profile).select_related(
            "order", "order__store"
        )
        data = []
        for a in qs:
            data.append(
                {
                    "id": str(a.id),
                    "orderId": str(a.order_id),
                    "storeName": a.order.store.name,
                    "customerAddress": a.order.address_snapshot.get("line1", ""),
                    "status": a.order.status,
                    "pickupConfirmed": a.pickup_confirmed_at is not None,
                    "deliveryConfirmed": a.delivered_at is not None,
                    "earnings": float(a.driver_earnings),
                }
            )
        return Response(data)


class AssignmentDetailView(APIView):
    permission_classes = [IsAuthenticated, IsDeliveryPartner]

    def get(self, request, assignment_id):
        assignment = (
            DeliveryAssignment.objects.filter(id=assignment_id, partner=request.user.delivery_profile)
            .select_related("order", "order__store", "order__customer")
            .first()
        )
        if not assignment:
            return Response({"message": "Not found", "code": "not_found"}, status=404)
        order = assignment.order
        addr = order.address_snapshot
        store = order.store
        return Response(
            {
                "id": str(assignment.id),
                "displayId": order.display_id,
                "estimatedMinutes": "15-20",
                "distanceMiles": 2.4,
                "mapImageUrl": "https://picsum.photos/seed/route/800/500",
                "pickup": {
                    "storeName": store.name,
                    "address": f"{store.latitude}, {store.longitude}",
                    "phone": store.owner.user.phone,
                },
                "delivery": {
                    "customerName": order.customer.name,
                    "address": f"{addr.get('line1', '')}, {addr.get('city', '')}",
                    "instructions": addr.get("label", ""),
                },
                "items": [
                    {
                        "id": str(item.id),
                        "name": item.product_name,
                        "unit": item.unit,
                        "quantity": item.quantity,
                        "imageUrl": item.image_url or f"https://picsum.photos/seed/{item.id}/100/100",
                    }
                    for item in order.items.all()
                ],
                "subtotal": float(order.subtotal),
                "driverEarnings": float(assignment.driver_earnings),
                "pickupConfirmed": assignment.pickup_confirmed_at is not None,
                "status": order.status,
            }
        )


class ConfirmPickupView(APIView):
    permission_classes = [IsAuthenticated, IsDeliveryPartner]

    def post(self, request, assignment_id):
        assignment = DeliveryAssignment.objects.filter(
            id=assignment_id, partner=request.user.delivery_profile
        ).first()
        if not assignment:
            return Response({"message": "Not found", "code": "not_found"}, status=404)
        assignment.pickup_confirmed_at = timezone.now()
        assignment.save()
        transition_order(assignment.order, OrderStatus.OUT_FOR_DELIVERY, request.user, "Picked up")
        return Response(serialize_order(assignment.order, request))


class ConfirmDeliverView(APIView):
    permission_classes = [IsAuthenticated, IsDeliveryPartner]

    def post(self, request, assignment_id):
        assignment = DeliveryAssignment.objects.filter(
            id=assignment_id, partner=request.user.delivery_profile
        ).first()
        if not assignment:
            return Response({"message": "Not found", "code": "not_found"}, status=404)
        assignment.delivered_at = timezone.now()
        assignment.save()
        transition_order(assignment.order, OrderStatus.DELIVERED, request.user, "Delivered")
        return Response(serialize_order(assignment.order, request))


class DeliveryEarningsView(APIView):
    permission_classes = [IsAuthenticated, IsDeliveryPartner]

    def get(self, request):
        profile = request.user.delivery_profile
        now = timezone.now()
        week_start = now - timezone.timedelta(days=7)
        month_start = now - timezone.timedelta(days=30)
        today_qs = DeliveryAssignment.objects.filter(partner=profile, assigned_at__date=now.date())
        week_qs = DeliveryAssignment.objects.filter(partner=profile, assigned_at__gte=week_start)
        month_qs = DeliveryAssignment.objects.filter(partner=profile, assigned_at__gte=month_start)
        return Response(
            {
                "today": float(today_qs.aggregate(t=Sum("driver_earnings"))["t"] or 0),
                "week": float(week_qs.aggregate(t=Sum("driver_earnings"))["t"] or 0),
                "month": float(month_qs.aggregate(t=Sum("driver_earnings"))["t"] or 0),
            }
        )


class DeliveryHistoryView(APIView):
    permission_classes = [IsAuthenticated, IsDeliveryPartner]

    def get(self, request):
        qs = (
            DeliveryAssignment.objects.filter(partner=request.user.delivery_profile, delivered_at__isnull=False)
            .select_related("order")
            .order_by("-delivered_at")[:50]
        )
        return Response(
            [
                {
                    "id": str(a.id),
                    "orderId": str(a.order_id),
                    "displayId": a.order.display_id,
                    "earnings": float(a.driver_earnings),
                    "deliveredAt": a.delivered_at.isoformat() if a.delivered_at else None,
                }
                for a in qs
            ]
        )
