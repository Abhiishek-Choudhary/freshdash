from apps.cart.models import Cart, CartItem
from apps.catalog.models import Product
from apps.catalog.serializers import ProductSerializer


def get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def cart_items_response(cart, request=None):
    items = []
    for item in cart.items.select_related("product", "product__store"):
        product_data = ProductSerializer(item.product, context={"request": request}).data
        items.append(
            {
                "productId": str(item.product_id),
                "product": product_data,
                "quantity": item.quantity,
            }
        )
    return items


def sync_cart(user, items_data, request=None):
    cart = get_or_create_cart(user)
    cart.items.all().delete()
    for entry in items_data:
        product_id = entry.get("productId") or entry.get("product_id")
        quantity = int(entry.get("quantity", 1))
        if not product_id:
            continue
        product = Product.objects.filter(id=product_id, is_deleted=False).first()
        if product and quantity > 0:
            CartItem.objects.create(cart=cart, product=product, quantity=quantity)
    return cart_items_response(cart, request)
