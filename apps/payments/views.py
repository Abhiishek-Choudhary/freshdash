from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.exceptions import APIError
from apps.orders.models import Order, PaymentMethod, PaymentStatus
from apps.payments.models import Payment
from apps.payments.services import create_payment_intent, mark_payment_paid, wallet_snapshot


class WalletView(APIView):
    """Ledger snapshot for the authenticated user — balance + recent entries."""

    def get(self, request):
        return Response(wallet_snapshot(request.user))


class PaymentCreateView(APIView):
    def post(self, request):
        order_id = request.data.get("orderId") or request.data.get("order_id")
        provider = request.data.get("provider")
        order = Order.objects.filter(id=order_id, customer=request.user).first()
        if not order:
            raise APIError("Order not found", code="not_found", status_code=404)
        if order.payment_method == PaymentMethod.COD:
            return Response(create_payment_intent(order, provider))
        if order.payment_status == PaymentStatus.PAID:
            return Response({"paymentRequired": False, "status": "paid", "orderId": str(order.id)})
        return Response(create_payment_intent(order, provider))


class PaymentConfirmView(APIView):
    """Dev/mock confirm — production should use provider webhooks only."""

    def post(self, request):
        payment_id = request.data.get("paymentId") or request.data.get("payment_id")
        payment = Payment.objects.filter(id=payment_id, order__customer=request.user).first()
        if not payment:
            raise APIError("Payment not found", code="not_found", status_code=404)
        mark_payment_paid(payment)
        return Response(
            {
                "paymentId": str(payment.id),
                "status": payment.status,
                "orderId": str(payment.order_id),
            }
        )


class PaymentWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, provider):
        payment_id = request.data.get("paymentId") or request.data.get("payment_id")
        external_id = request.data.get("externalId") or request.data.get("external_id")
        payment = None
        if payment_id:
            payment = Payment.objects.filter(id=payment_id).first()
        elif external_id:
            payment = Payment.objects.filter(external_id=external_id, provider=provider).first()
        if payment:
            mark_payment_paid(payment)
        return Response({"received": True})
