from apps.notifications.models import Notification
from apps.orders.models import OrderStatusLog


def notify_order_status(log: OrderStatusLog):
    order = log.order
    user = order.customer
    Notification.objects.create(
        user=user,
        type="order",
        title=f"Order {order.display_id} updated",
        body=f"Your order is now: {log.to_status.replace('_', ' ')}",
        data={"orderId": str(order.id), "status": log.to_status},
    )
