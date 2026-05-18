from decimal import Decimal

from django.utils import timezone

from apps.delivery.models import DeliveryAssignment
from config.socketio_server import emit_delivery_location


def update_assignment_location(assignment: DeliveryAssignment, lat, lng):
    assignment.driver_latitude = Decimal(str(lat))
    assignment.driver_longitude = Decimal(str(lng))
    assignment.location_updated_at = timezone.now()
    assignment.save(update_fields=["driver_latitude", "driver_longitude", "location_updated_at"])
    emit_delivery_location(
        str(assignment.order_id),
        float(assignment.driver_latitude),
        float(assignment.driver_longitude),
    )
    return assignment
