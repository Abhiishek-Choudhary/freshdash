import logging

from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.exceptions import APIError
from apps.orders.models import Order, PaymentMethod, PaymentStatus
from apps.payments.models import Payment, PaymentProvider
from apps.payments.services import (
    create_payment_intent,
    mark_payment_paid,
    verify_razorpay_payment_signature,
    verify_razorpay_webhook_signature,
    wallet_snapshot,
)

logger = logging.getLogger(__name__)


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
    """Client-side confirm — mostly used in dev/mock. Production relies on the
    signed webhook (below) as the authoritative source of truth; this endpoint
    stays fast so the UI can advance without waiting for the webhook round-trip.

    When the client forwards razorpayPaymentId + signature and a webhook secret
    is configured, we verify the payment signature (belt-and-braces). Missing
    signature is tolerated so the mock provider path still works.
    """

    def post(self, request):
        payment_id = request.data.get("paymentId") or request.data.get("payment_id")
        payment = Payment.objects.filter(id=payment_id, order__customer=request.user).first()
        if not payment:
            raise APIError("Payment not found", code="not_found", status_code=404)

        rp_payment_id = request.data.get("razorpayPaymentId") or request.data.get("razorpay_payment_id")
        signature = request.data.get("signature") or request.data.get("razorpay_signature")

        if payment.provider == PaymentProvider.RAZORPAY and rp_payment_id and signature:
            if not verify_razorpay_payment_signature(
                order_id=payment.external_id,
                payment_id=rp_payment_id,
                signature=signature,
            ):
                logger.warning(
                    "Razorpay signature mismatch on confirm for payment %s", payment.id
                )
                raise APIError(
                    "Payment signature verification failed",
                    code="invalid_signature",
                    status_code=400,
                )

        mark_payment_paid(payment)
        return Response(
            {
                "paymentId": str(payment.id),
                "status": payment.status,
                "orderId": str(payment.order_id),
            }
        )


class PaymentWebhookView(APIView):
    """Provider-initiated webhook. Authoritative source of payment status.

    For Razorpay: verifies X-Razorpay-Signature against RAZORPAY_WEBHOOK_SECRET,
    then marks the matching Payment as paid on `payment.captured` events. If no
    secret is configured, the endpoint refuses to trust the payload — set the
    secret in the Razorpay Dashboard and mirror it in the env before going live.
    """

    authentication_classes = []
    permission_classes = []

    def post(self, request, provider):
        if provider == PaymentProvider.RAZORPAY:
            return self._handle_razorpay(request)

        # Legacy dev/mock branch — accepts a bare paymentId body.
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

    def _handle_razorpay(self, request):
        secret = getattr(settings, "RAZORPAY_WEBHOOK_SECRET", "")
        if not secret:
            logger.error("Razorpay webhook received but RAZORPAY_WEBHOOK_SECRET is unset")
            return Response(
                {"message": "Webhook not configured", "code": "not_configured"},
                status=503,
            )
        signature = request.META.get("HTTP_X_RAZORPAY_SIGNATURE", "")
        raw_body = request.body  # bytes
        if not verify_razorpay_webhook_signature(raw_body, signature, secret):
            logger.warning("Razorpay webhook signature mismatch")
            return Response(
                {"message": "Invalid signature", "code": "invalid_signature"},
                status=400,
            )

        # request.data was already parsed from raw_body; use it now that the
        # signature has been validated against the exact bytes.
        event = request.data.get("event") or ""
        payload = request.data.get("payload") or {}
        entity = ((payload.get("payment") or {}).get("entity")) or {}
        rp_order_id = entity.get("order_id") or ""
        rp_payment_id = entity.get("id") or ""

        payment = None
        if rp_order_id:
            payment = Payment.objects.filter(
                external_id=rp_order_id, provider=PaymentProvider.RAZORPAY
            ).first()
        if not payment:
            logger.info("Razorpay webhook: no matching payment for order %s", rp_order_id)
            return Response({"received": True, "matched": False})

        if event in ("payment.captured", "order.paid"):
            mark_payment_paid(payment)
            if rp_payment_id and payment.external_id != rp_payment_id:
                # Store the Razorpay payment id (distinct from the order id we
                # originally saved) so it's easy to reconcile in the dashboard.
                payment.metadata = {**(payment.metadata or {}), "razorpay_payment_id": rp_payment_id}
                payment.save(update_fields=["metadata", "updated_at"])
        elif event == "payment.failed":
            payment.status = PaymentStatus.PENDING
            payment.metadata = {
                **(payment.metadata or {}),
                "razorpay_payment_id": rp_payment_id,
                "failure": entity.get("error_description") or entity.get("error_reason") or "failed",
            }
            payment.save(update_fields=["status", "metadata", "updated_at"])

        return Response({"received": True, "matched": True, "event": event})
