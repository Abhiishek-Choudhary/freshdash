from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.notifications.services import notify_order_status
from apps.orders.models import OrderStatus, OrderStatusLog
from config.socketio_server import emit_order_update


@receiver(post_save, sender=OrderStatusLog)
def on_status_log(sender, instance, created, **kwargs):
    if not created:
        return
    emit_order_update(str(instance.order_id), instance.to_status, instance.note or "")
    notify_order_status(instance)

    order = instance.order
    if instance.to_status == OrderStatus.DELIVERED:
        # Money moves at delivery time: seller earns their share, delivery
        # partner earns theirs, and for COD the buyer is finally charged.
        try:
            from apps.orders.models import PaymentMethod, PaymentStatus
            from apps.payments.services import (
                record_delivery_earnings,
                record_order_charge,
                record_seller_payout,
            )

            if order.payment_method == PaymentMethod.COD:
                order.payment_status = PaymentStatus.PAID
                order.save(update_fields=["payment_status", "updated_at"])
                record_order_charge(order)
            record_seller_payout(order)
            assignment = getattr(order, "delivery_assignment", None)
            if assignment:
                record_delivery_earnings(assignment)
        except Exception:
            pass
    elif instance.to_status == OrderStatus.CANCELLED:
        # If we already collected money from the buyer, refund it back into
        # their wallet ledger.
        try:
            from apps.orders.models import PaymentStatus
            from apps.payments.services import record_order_refund

            if order.payment_status == PaymentStatus.REFUNDED:
                record_order_refund(order)
        except Exception:
            pass
