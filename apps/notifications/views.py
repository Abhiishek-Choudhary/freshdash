from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.models import Notification


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
