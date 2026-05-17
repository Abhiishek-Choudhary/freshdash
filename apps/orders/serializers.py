from apps.catalog.serializers import ProductSerializer
from apps.orders.models import Address, Order, OrderItem


def serialize_order_item(item: OrderItem, request=None):
    product_data = None
    if item.product and not item.product.is_deleted:
        product_data = ProductSerializer(item.product, context={"request": request}).data
    else:
        product_data = {
            "id": str(item.product_id) if item.product_id else "",
            "storeId": "",
            "name": item.product_name,
            "description": "",
            "imageUrl": item.image_url or f"https://picsum.photos/seed/{item.id}/200/200",
            "price": float(item.unit_price),
            "unit": item.unit,
            "category": "",
            "inStock": False,
            "stockCount": 0,
        }
    return {
        "productId": str(item.product_id) if item.product_id else product_data["id"],
        "product": product_data,
        "quantity": item.quantity,
    }


def serialize_order(order: Order, request=None):
    items = [serialize_order_item(i, request) for i in order.items.all()]
    data = {
        "id": str(order.id),
        "displayId": order.display_id,
        "storeId": str(order.store_id),
        "storeName": order.store.name,
        "items": items,
        "status": order.status,
        "address": order.address_snapshot,
        "summary": {
            "subtotal": float(order.subtotal),
            "deliveryFee": float(order.delivery_fee),
            "taxes": float(order.taxes),
            "discount": float(order.discount),
            "total": float(order.total),
        },
        "createdAt": order.created_at.isoformat(),
    }
    if order.estimated_delivery_at:
        data["estimatedDelivery"] = order.estimated_delivery_at.isoformat()
    if order.delivery_window_label:
        data["estimatedDeliveryWindow"] = order.delivery_window_label
    assignment = getattr(order, "delivery_assignment", None)
    if assignment and assignment.partner:
        partner_user = assignment.partner.user
        data["deliveryPartner"] = {
            "id": str(partner_user.id),
            "name": partner_user.name,
            "avatarUrl": "",
            "rating": float(assignment.partner.rating),
            "title": "Your Delivery Hero",
        }
    return data


class AddressSerializer:
    @staticmethod
    def to_representation(address: Address):
        return {
            "id": str(address.id),
            "label": address.label,
            "line1": address.line1,
            "line2": address.line2,
            "city": address.city,
            "state": address.state,
            "zipCode": address.zip_code,
            "isDefault": address.is_default,
        }

    @staticmethod
    def from_request(data):
        return {
            "label": data.get("label", "Home"),
            "line1": data.get("line1") or data.get("line_1", ""),
            "line2": data.get("line2") or data.get("line_2", ""),
            "city": data.get("city", ""),
            "state": data.get("state", ""),
            "zip_code": data.get("zipCode") or data.get("zip_code", ""),
            "is_default": data.get("isDefault", data.get("is_default", False)),
        }
