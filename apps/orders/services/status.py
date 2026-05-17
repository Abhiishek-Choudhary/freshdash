from apps.accounts.exceptions import APIError
from apps.orders.models import Order, OrderStatus, OrderStatusLog

TRANSITIONS = {
    OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.PREPARING, OrderStatus.CANCELLED},
    OrderStatus.PREPARING: {OrderStatus.READY_FOR_PICKUP, OrderStatus.CANCELLED},
    OrderStatus.READY_FOR_PICKUP: {OrderStatus.OUT_FOR_DELIVERY},
    OrderStatus.OUT_FOR_DELIVERY: {OrderStatus.DELIVERED},
}


def transition_order(order: Order, new_status: str, user=None, note: str = ""):
    allowed = TRANSITIONS.get(order.status, set())
    if new_status not in allowed and not (user and user.is_superuser):
        raise APIError(
            f"Cannot transition from {order.status} to {new_status}",
            code="invalid_transition",
            status_code=400,
        )
    old = order.status
    order.status = new_status
    if new_status == OrderStatus.CANCELLED:
        from django.utils import timezone

        order.cancelled_at = timezone.now()
        order.cancellation_reason = note
    order.save()
    log = OrderStatusLog.objects.create(
        order=order,
        from_status=old,
        to_status=new_status,
        changed_by=user,
        note=note,
    )
    return log
