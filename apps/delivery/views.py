from decimal import Decimal

from django.conf import settings
from django.db.models import Sum
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsDeliveryPartner
from apps.accounts.utils import get_user_store
from apps.delivery.models import BidStatus, DeliveryAssignment, DeliveryBid
from apps.orders.models import Order, OrderStatus
from apps.orders.serializers import serialize_order
from apps.delivery.location import update_assignment_location
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


class AssignmentLocationView(APIView):
    permission_classes = [IsAuthenticated, IsDeliveryPartner]

    def patch(self, request, assignment_id):
        lat = request.data.get("lat")
        lng = request.data.get("lng")
        if lat is None or lng is None:
            return Response(
                {"message": "lat and lng required", "code": "validation_error"},
                status=400,
            )
        assignment = DeliveryAssignment.objects.filter(
            id=assignment_id, partner=request.user.delivery_profile
        ).first()
        if not assignment:
            return Response({"message": "Not found", "code": "not_found"}, status=404)
        update_assignment_location(assignment, lat, lng)
        return Response(
            {
                "orderId": str(assignment.order_id),
                "lat": float(assignment.driver_latitude),
                "lng": float(assignment.driver_longitude),
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


# ---------------------------------------------------------------------------
# Delivery bidding
# ---------------------------------------------------------------------------


def _bid_dict(bid: DeliveryBid) -> dict:
    partner = bid.partner
    user = getattr(partner, "user", None)
    return {
        "id": str(bid.id),
        "orderId": str(bid.order_id),
        "amount": float(bid.amount),
        "etaMinutes": bid.eta_minutes,
        "note": bid.note,
        "status": bid.status,
        "createdAt": bid.created_at.isoformat(),
        "partner": {
            "id": str(partner.id),
            "name": user.name if user else "Partner",
            "rating": float(partner.rating or 0),
            "vehicleType": partner.vehicle_type or "",
        },
    }


class OpenPickupsView(APIView):
    """Orders that are ready for pickup and have no active assignment yet."""

    permission_classes = [IsAuthenticated, IsDeliveryPartner]

    def get(self, request):
        qs = (
            Order.objects.filter(status=OrderStatus.READY_FOR_PICKUP, delivery_assignment__isnull=True)
            .select_related("store")
            .prefetch_related("delivery_bids")[:50]
        )
        me = request.user.delivery_profile
        data = []
        for order in qs:
            my_bid = next((b for b in order.delivery_bids.all() if b.partner_id == me.id), None)
            data.append(
                {
                    "id": str(order.id),
                    "displayId": order.display_id,
                    "storeName": order.store.name,
                    "customerAddress": order.address_snapshot.get("line1", ""),
                    "itemCount": order.items.count(),
                    "total": float(order.total),
                    "suggestedFee": float(order.delivery_fee),
                    "bidsCount": order.delivery_bids.count(),
                    "myBid": _bid_dict(my_bid) if my_bid else None,
                    "createdAt": order.created_at.isoformat(),
                }
            )
        return Response(data)


class BidCreateView(APIView):
    """Delivery partner places a bid on an open pickup."""

    permission_classes = [IsAuthenticated, IsDeliveryPartner]

    def post(self, request):
        order_id = request.data.get("orderId") or request.data.get("order_id")
        amount = request.data.get("amount")
        eta = int(request.data.get("etaMinutes") or request.data.get("eta_minutes") or 30)
        note = (request.data.get("note") or "").strip()[:255]

        order = Order.objects.filter(id=order_id, status=OrderStatus.READY_FOR_PICKUP).first()
        if not order:
            return Response({"message": "Order not accepting bids", "code": "not_biddable"}, status=400)
        if hasattr(order, "delivery_assignment"):
            return Response({"message": "Order already assigned", "code": "already_assigned"}, status=400)
        try:
            amount_dec = Decimal(str(amount))
        except Exception:
            return Response({"message": "Invalid amount", "code": "validation_error"}, status=400)

        partner = request.user.delivery_profile
        bid, created = DeliveryBid.objects.update_or_create(
            order=order,
            partner=partner,
            defaults={
                "amount": amount_dec,
                "eta_minutes": eta,
                "note": note,
                "status": BidStatus.OPEN,
            },
        )
        return Response(_bid_dict(bid), status=201 if created else 200)


class OrderBidsView(APIView):
    """List bids on an order — visible to the buyer, seller of the store, or admin."""

    def get(self, request, order_id):
        order = Order.objects.filter(id=order_id).select_related("store").first()
        if not order:
            return Response({"message": "Not found", "code": "not_found"}, status=404)
        store = get_user_store(request.user)
        allowed = (
            order.customer_id == request.user.id
            or (store and store.id == order.store_id)
            or getattr(request.user, "is_superuser", False)
        )
        if not allowed:
            return Response({"message": "Forbidden", "code": "forbidden"}, status=403)
        bids = order.delivery_bids.select_related("partner", "partner__user").all()
        return Response([_bid_dict(b) for b in bids])


class BidAcceptView(APIView):
    """Seller (or buyer) accepts a bid → creates a DeliveryAssignment with the
    accepted amount as driver_earnings. Other open bids are marked rejected."""

    def post(self, request, bid_id):
        bid = DeliveryBid.objects.select_related("order", "partner").filter(id=bid_id).first()
        if not bid:
            return Response({"message": "Not found", "code": "not_found"}, status=404)
        order = bid.order
        store = get_user_store(request.user)
        allowed = (
            order.customer_id == request.user.id
            or (store and store.id == order.store_id)
            or getattr(request.user, "is_superuser", False)
        )
        if not allowed:
            return Response({"message": "Forbidden", "code": "forbidden"}, status=403)
        if hasattr(order, "delivery_assignment"):
            return Response({"message": "Already assigned", "code": "already_assigned"}, status=400)
        if bid.status != BidStatus.OPEN:
            return Response({"message": "Bid not open", "code": "invalid_state"}, status=400)

        assignment = DeliveryAssignment.objects.create(
            order=order,
            partner=bid.partner,
            driver_earnings=bid.amount,
        )
        bid.status = BidStatus.ACCEPTED
        bid.save(update_fields=["status"])
        DeliveryBid.objects.filter(order=order, status=BidStatus.OPEN).exclude(id=bid.id).update(
            status=BidStatus.REJECTED
        )

        try:
            from apps.notifications.services import notify_delivery_assigned

            notify_delivery_assigned(assignment)
        except Exception:
            pass
        return Response({"assignmentId": str(assignment.id), "orderId": str(order.id)})
