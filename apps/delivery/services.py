from django.conf import settings

from apps.accounts.models import DeliveryPartnerProfile
from apps.delivery.models import DeliveryAssignment
from apps.orders.models import Order


def create_assignment_for_order(order: Order):
    if hasattr(order, "delivery_assignment"):
        return order.delivery_assignment
    partner = DeliveryPartnerProfile.objects.filter(is_online=True).first()
    if not partner:
        partner = DeliveryPartnerProfile.objects.first()
    if not partner:
        return None
    assignment = DeliveryAssignment.objects.create(
        order=order,
        partner=partner,
        driver_earnings=settings.DRIVER_EARNINGS_FLAT,
    )
    # The READY_FOR_PICKUP status transition also fires notify_order_status,
    # but that runs before the assignment exists (assignment is created after
    # the transition inside VendorOrderActionView). Push explicitly here so the
    # partner gets a dedicated "new pickup" notification with the assignment id.
    try:
        from apps.notifications.services import notify_delivery_assigned

        notify_delivery_assigned(assignment)
    except Exception:
        # Don't let a notification failure roll back the assignment.
        pass
    return assignment
