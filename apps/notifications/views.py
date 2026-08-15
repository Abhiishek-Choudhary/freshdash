from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.models import Notification


class RegisterDeviceView(APIView):
    """Save the Expo push token for the authenticated user so backend
    can push order/delivery updates via https://exp.host/--/api/v2/push/send."""

    def post(self, request):
        token = (request.data.get("token") or "").strip()
        platform = (request.data.get("platform") or "").strip()
        if not token:
            return Response({"message": "token is required", "code": "validation_error"}, status=400)
        user = request.user
        user.expo_push_token = token
        user.device_platform = platform[:16]
        user.save(update_fields=["expo_push_token", "device_platform", "updated_at"])
        return Response({"success": True})


class NotificationListView(APIView):
    def get(self, request):
        qs = Notification.objects.filter(user=request.user)[:50]
        return Response(
            [
                {
                    "id": str(n.id),
                    "type": n.type,
                    "title": n.title,
                    "body": n.body,
                    "read": n.read,
                    "createdAt": n.created_at.isoformat(),
                    "data": n.data,
                }
                for n in qs
            ]
        )


class NotificationMarkReadView(APIView):
    def patch(self, request, notification_id):
        n = Notification.objects.filter(id=notification_id, user=request.user).first()
        if not n:
            return Response({"message": "Not found", "code": "not_found"}, status=404)
        n.read = True
        n.save(update_fields=["read"])
        return Response(
            {
                "id": str(n.id),
                "type": n.type,
                "title": n.title,
                "body": n.body,
                "read": n.read,
                "createdAt": n.created_at.isoformat(),
                "data": n.data,
            }
        )
