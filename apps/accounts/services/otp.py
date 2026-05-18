import hashlib
import random
import string
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from apps.accounts.exceptions import APIError
from apps.accounts.models import OtpChallenge, OtpPurpose


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def _rate_limit_key(phone: str) -> str:
    return f"otp_rate:{phone}"


def send_otp(phone: str, purpose: str) -> bool:
    from apps.accounts.managers import UserManager

    phone = UserManager.normalize_phone(phone)
    rate_key = _rate_limit_key(phone)
    count = cache.get(rate_key, 0)
    if count >= settings.OTP_RATE_LIMIT:
        raise APIError("Too many OTP requests. Try again later.", code="otp_rate_limited", status_code=429)

    if settings.OTP_DEV_CODE:
        code = settings.OTP_DEV_CODE
    else:
        code = "".join(random.choices(string.digits, k=6))

    OtpChallenge.objects.filter(phone=phone, purpose=purpose, consumed=False).update(consumed=True)
    OtpChallenge.objects.create(
        phone=phone,
        code_hash=_hash_code(code),
        purpose=purpose,
        expires_at=timezone.now() + timedelta(seconds=settings.OTP_EXPIRY_SECONDS),
    )
    cache.set(rate_key, count + 1, timeout=3600)
    if not settings.OTP_DEV_CODE:
        from apps.accounts.services.sms import send_sms

        send_sms(phone, f"Your FreshDash OTP is {code}. Valid for {settings.OTP_EXPIRY_SECONDS // 60} minutes.")
    return True


def verify_otp(phone: str, otp: str, purpose: str) -> bool:
    from apps.accounts.managers import UserManager

    phone = UserManager.normalize_phone(phone)
    challenge = (
        OtpChallenge.objects.filter(phone=phone, purpose=purpose, consumed=False)
        .order_by("-created_at")
        .first()
    )
    if not challenge:
        raise APIError("Invalid or expired OTP", code="invalid_otp", status_code=400)
    if timezone.now() > challenge.expires_at:
        raise APIError("OTP has expired", code="otp_expired", status_code=400)
    challenge.attempts += 1
    challenge.save(update_fields=["attempts"])
    if challenge.attempts > 5:
        challenge.consumed = True
        challenge.save(update_fields=["consumed"])
        raise APIError("Too many attempts", code="otp_locked", status_code=400)
    if challenge.code_hash != _hash_code(otp):
        raise APIError("Invalid OTP", code="invalid_otp", status_code=400)
    challenge.consumed = True
    challenge.save(update_fields=["consumed"])
    return True
