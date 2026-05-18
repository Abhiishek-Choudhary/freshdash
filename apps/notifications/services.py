from apps.notifications.models import Notification
from apps.orders.models import OrderStatusLog
from config.socketio_server import emit_notification_new


def notify_order_status(log: OrderStatusLog):
    order = log.order
    user = order.customer
    notification = Notification.objects.create(
        user=user,
        type="order",
        title=f"Order {order.display_id} updated",
        body=f"Your order is now: {log.to_status.replace('_', ' ')}",
        data={"orderId": str(order.id), "status": log.to_status},
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
    from apps.notifications.push import send_push_to_user

    send_push_to_user(user, notification.title, notification.body, notification.data)
