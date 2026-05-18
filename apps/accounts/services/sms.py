import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def send_sms(phone: str, message: str) -> bool:
    provider = getattr(settings, "SMS_PROVIDER", "").lower()
    if provider == "twilio":
        return _send_twilio(phone, message)
    if provider in ("msg91", "msg"):
        return _send_msg91(phone, message)
    logger.info("SMS provider not configured; would send to %s: %s", phone, message)
    return False


def _send_twilio(phone: str, message: str) -> bool:
    account_sid = getattr(settings, "TWILIO_ACCOUNT_SID", "")
    auth_token = getattr(settings, "TWILIO_AUTH_TOKEN", "")
    from_number = getattr(settings, "TWILIO_FROM_NUMBER", "")
    if not all([account_sid, auth_token, from_number]):
        return False
    try:
        from twilio.rest import Client

        Client(account_sid, auth_token).messages.create(
            body=message, from_=from_number, to=phone
        )
        return True
    except Exception as exc:
        logger.warning("Twilio SMS failed: %s", exc)
        return False


def _send_msg91(phone: str, message: str) -> bool:
    auth_key = getattr(settings, "MSG91_AUTH_KEY", "")
    sender = getattr(settings, "MSG91_SENDER_ID", "FRESHD")
    template_id = getattr(settings, "MSG91_OTP_TEMPLATE_ID", "")
    if not auth_key:
        return False
    try:
        import requests

        response = requests.post(
            "https://control.msg91.com/api/v5/flow/",
            headers={"authkey": auth_key, "Content-Type": "application/json"},
            json={
                "template_id": template_id,
                "short_url": "0",
                "recipients": [{"mobiles": phone.lstrip("+"), "otp": message}],
                "sender": sender,
            },
            timeout=10,
        )
        return response.ok
    except Exception as exc:
        logger.warning("MSG91 SMS failed: %s", exc)
        return False
