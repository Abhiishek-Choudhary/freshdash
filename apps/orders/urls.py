from django.urls import path

from apps.orders import views

urlpatterns = [
    path("addresses", views.AddressListCreateView.as_view()),
    path("addresses/<uuid:address_id>", views.AddressDetailView.as_view()),
    path("orders", views.OrderListCreateView.as_view()),
    path("orders/<uuid:order_id>", views.OrderDetailView.as_view()),
    path("orders/<uuid:order_id>/cancel", views.OrderCancelView.as_view()),
    path("orders/<uuid:order_id>/track", views.OrderTrackView.as_view()),
    path("checkout/slots", views.CheckoutSlotsView.as_view()),
    path("checkout/preview", views.CheckoutPreviewView.as_view()),
    path("coupons/validate", views.CouponValidateView.as_view()),
    path("vendor/dashboard", views.VendorDashboardView.as_view()),
    path("vendor/orders", views.VendorOrderListView.as_view()),
    path("vendor/orders/<uuid:order_id>/accept", views.VendorOrderActionView.as_view(), {"action": "accept"}),
    path("vendor/orders/<uuid:order_id>/prepare", views.VendorOrderActionView.as_view(), {"action": "prepare"}),
    path("vendor/orders/<uuid:order_id>/reject", views.VendorOrderActionView.as_view(), {"action": "reject"}),
    path("vendor/orders/<uuid:order_id>/ready", views.VendorOrderActionView.as_view(), {"action": "ready"}),
    path("vendor/analytics", views.VendorAnalyticsView.as_view()),
    path("vendor/earnings", views.VendorEarningsView.as_view()),
]
