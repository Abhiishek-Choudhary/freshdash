from django.conf import settings

from apps.accounts.models import DeliveryPartnerProfile
from apps.delivery.models import DeliveryAssignment
from apps.orders.models import Order, OrderStatus


def create_assignment_for_order(order: Order):
    if hasattr(order, "delivery_assignment"):
        return order.delivery_assignment
    partner = DeliveryPartnerProfile.objects.filter(is_online=True).first()
    if not partner:
        partner = DeliveryPartnerProfile.objects.first()
    if not partner:
        return None
    return DeliveryAssignment.objects.create(
        order=order,
        partner=partner,
        driver_earnings=settings.DRIVER_EARNINGS_FLAT,
    )
