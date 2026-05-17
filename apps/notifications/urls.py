from django.urls import path

from apps.notifications import views

urlpatterns = [
    path("notifications", views.NotificationListView.as_view()),
    path("notifications/<uuid:notification_id>/read", views.NotificationMarkReadView.as_view()),
]
