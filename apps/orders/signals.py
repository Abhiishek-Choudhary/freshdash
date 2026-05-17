from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.notifications.services import notify_order_status
from apps.orders.models import OrderStatusLog
from config.socketio_server import emit_order_update


@receiver(post_save, sender=OrderStatusLog)
def on_status_log(sender, instance, created, **kwargs):
    if not created:
        return
    emit_order_update(str(instance.order_id), instance.to_status, instance.note or "")
    notify_order_status(instance)
