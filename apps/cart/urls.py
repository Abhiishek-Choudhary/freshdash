from django.urls import path

from apps.cart import views

urlpatterns = [
    path("cart", views.CartView.as_view()),
    path("cart/sync", views.CartSyncView.as_view()),
]
