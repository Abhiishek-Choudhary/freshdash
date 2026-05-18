import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def send_push_to_user(user, title: str, body: str, data: dict | None = None):
    token = getattr(user, "fcm_token", None)
    server_key = getattr(settings, "FCM_SERVER_KEY", "")
    if not server_key:
        logger.debug("FCM_SERVER_KEY not set; skip push for user %s", user.id)
        return False
    if not token:
        logger.debug("No FCM token for user %s", user.id)
        return False
    try:
        import requests

        response = requests.post(
            "https://fcm.googleapis.com/fcm/send",
            headers={
                "Authorization": f"key={server_key}",
                "Content-Type": "application/json",
            },
            json={
                "to": token,
                "notification": {"title": title, "body": body},
                "data": data or {},
            },
            timeout=10,
        )
        return response.ok
    except Exception as exc:
        logger.warning("FCM push failed: %s", exc)
        return False
