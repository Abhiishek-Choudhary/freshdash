from django.utils import timezone

from apps.orders.models import OrderStatus


def user_avatar_url(user, request=None):
    if user.avatar:
        if request:
            return request.build_absolute_uri(user.avatar.url)
        return user.avatar.url
    return f"https://picsum.photos/seed/{user.id}/200/200"


def compute_is_on_time(order) -> bool | None:
    if not order.estimated_delivery_at:
        return None
    now = timezone.now()
    if order.status == OrderStatus.DELIVERED:
        return now <= order.estimated_delivery_at
    if order.status == OrderStatus.CANCELLED:
        return None
    return now <= order.estimated_delivery_at


def driver_location_payload(assignment):
    if assignment.driver_latitude is None or assignment.driver_longitude is None:
        return None
    return {
        "lat": float(assignment.driver_latitude),
        "lng": float(assignment.driver_longitude),
        "updatedAt": assignment.location_updated_at.isoformat()
        if assignment.location_updated_at
        else None,
    }
