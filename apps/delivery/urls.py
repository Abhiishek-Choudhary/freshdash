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
    # Bidding marketplace
    path("delivery/open-pickups", views.OpenPickupsView.as_view()),
    path("delivery/bids", views.BidCreateView.as_view()),
    path("delivery/bids/<uuid:bid_id>/accept", views.BidAcceptView.as_view()),
    path("orders/<uuid:order_id>/bids", views.OrderBidsView.as_view()),
]
