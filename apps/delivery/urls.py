from django.urls import path

from apps.delivery import views

urlpatterns = [
    path("delivery/dashboard", views.DeliveryDashboardView.as_view()),
    path("delivery/partner/online", views.PartnerOnlineView.as_view()),
    path("delivery/assignments", views.AssignmentListView.as_view()),
    path("delivery/assignments/<uuid:assignment_id>", views.AssignmentDetailView.as_view()),
    path(
        "delivery/assignments/<uuid:assignment_id>/location",
        views.AssignmentLocationView.as_view(),
    ),
    path("delivery/assignments/<uuid:assignment_id>/pickup", views.ConfirmPickupView.as_view()),
    path("delivery/assignments/<uuid:assignment_id>/deliver", views.ConfirmDeliverView.as_view()),
    path("delivery/earnings", views.DeliveryEarningsView.as_view()),
    path("delivery/history", views.DeliveryHistoryView.as_view()),
]
