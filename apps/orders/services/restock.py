from apps.catalog.models import Product
from apps.orders.models import OrderItem


def restock_order_items(order):
    for item in order.items.all():
        if item.product_id:
            product = Product.objects.filter(id=item.product_id).first()
            if product:
                product.stock_count += item.quantity
                product.in_stock = True
                product.save(update_fields=["stock_count", "in_stock", "updated_at"])
