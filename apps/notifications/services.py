from apps.notifications.models import Notification
from apps.notifications.push import send_push_to_user
from apps.orders.models import OrderStatus, OrderStatusLog
from config.socketio_server import emit_notification_new


def _send(user, title: str, body: str, data: dict):
    if user is None:
        return
    notification = Notification.objects.create(
        user=user,
        type=data.get("type", "order"),
        title=title,
        body=body,
        data=data,
    )
    payload = {
        "id": str(notification.id),
        "type": notification.type,
        "title": notification.title,
        "body": notification.body,
        "read": notification.read,
        "createdAt": notification.created_at.isoformat(),
        "data": notification.data,
    }
    emit_notification_new(str(user.id), payload)
    send_push_to_user(user, notification.title, notification.body, notification.data)


# Copy per status per role. Only listed roles get notified for that status.
STATUS_COPY = {
    OrderStatus.PENDING: {
        "buyer": ("Order placed", "We've sent your order to the seller for confirmation."),
        "seller": ("New order received", "You have a new order — accept or reject in the Orders tab."),
    },
    OrderStatus.CONFIRMED: {
        "buyer": ("Order confirmed", "The seller accepted your order and will start preparing it."),
    },
    OrderStatus.PREPARING: {
        "buyer": ("Being prepared", "Your groceries are being packed."),
    },
    OrderStatus.READY_FOR_PICKUP: {
        "buyer": ("Ready for delivery", "Your order is packed and waiting for a delivery partner."),
        "delivery": ("New pickup", "A packed order is ready for pickup near you."),
    },
    OrderStatus.OUT_FOR_DELIVERY: {
        "buyer": ("On the way", "A delivery partner picked up your order."),
        "seller": ("Order picked up", "The delivery partner has picked up the order."),
    },
    OrderStatus.DELIVERED: {
        "buyer": ("Delivered", "Your order has been delivered. Enjoy!"),
        "seller": ("Order delivered", "Your order was successfully delivered."),
        "delivery": ("Delivery complete", "Nice work — earnings updated."),
    },
    OrderStatus.CANCELLED: {
        "buyer": ("Order cancelled", "Your order was cancelled."),
        "seller": ("Order cancelled", "An order was cancelled."),
    },
}


def _seller_user(order):
    profile = getattr(order.store, "owner", None)
    return getattr(profile, "user", None) if profile else None


def _delivery_user(order):
    assignment = getattr(order, "delivery_assignment", None)
    if not assignment or not assignment.partner:
        return None
    return getattr(assignment.partner, "user", None)


def notify_order_status(log: OrderStatusLog):
    """Fan out notifications for a status transition to every relevant role."""
    order = log.order
    copy = STATUS_COPY.get(log.to_status, {})
    common = {
        "type": "order",
        "orderId": str(order.id),
        "displayId": order.display_id,
        "status": log.to_status,
    }

    if "buyer" in copy:
        title, body = copy["buyer"]
        _send(order.customer, title, body, common)

    if "seller" in copy:
        title, body = copy["seller"]
        _send(_seller_user(order), title, body, common)

    if "delivery" in copy:
        title, body = copy["delivery"]
        _send(_delivery_user(order), title, body, common)


def notify_delivery_assigned(assignment):
    """Direct push when a delivery partner is assigned to an order."""
    order = assignment.order
    user = getattr(assignment.partner, "user", None) if assignment.partner else None
    if user is None:
        return
    _send(
        user,
        "New delivery assigned",
        f"Pickup at {order.store.name} — {order.items.count()} items.",
        {
            "type": "delivery",
            "assignmentId": str(assignment.id),
            "orderId": str(order.id),
            "displayId": order.display_id,
        },
    )
