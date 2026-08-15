import logging

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


def send_push_to_user(user, title: str, body: str, data: dict | None = None) -> bool:
    """Send a push notification via Expo's push service.

    Requires the user has previously registered an Expo push token via
    POST /api/notifications/device. Returns True on 200 response from Expo
    (does not guarantee device delivery — check receipts for that).
    """
    token = getattr(user, "expo_push_token", "") or ""
    if not token:
        logger.debug("No Expo push token for user %s", getattr(user, "id", "?"))
        return False
    if not token.startswith("ExponentPushToken[") and not token.startswith("ExpoPushToken["):
        logger.warning("Invalid Expo push token format for user %s", user.id)
        return False
    try:
        import requests

        payload = {
            "to": token,
            "title": title,
            "body": body,
            "sound": "default",
            "priority": "high",
            "data": data or {},
        }
        response = requests.post(
            EXPO_PUSH_URL,
            headers={
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=10,
        )
        if not response.ok:
            logger.warning(
                "Expo push HTTP %s for user %s: %s",
                response.status_code,
                user.id,
                response.text[:300],
            )
            return False
        result = response.json().get("data") or {}
        if isinstance(result, dict) and result.get("status") == "error":
            logger.warning("Expo push error for user %s: %s", user.id, result.get("message"))
            return False
        return True
    except Exception as exc:
        logger.exception("Expo push failed for user %s: %s", getattr(user, "id", "?"), exc)
        return False
