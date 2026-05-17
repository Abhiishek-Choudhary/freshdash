from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cart.services import cart_items_response, get_or_create_cart, sync_cart


class CartView(APIView):
    def get(self, request):
        cart = get_or_create_cart(request.user)
        return Response(cart_items_response(cart, request))


class CartSyncView(APIView):
    def post(self, request):
        items = request.data.get("items", [])
        return Response(sync_cart(request.user, items, request))
