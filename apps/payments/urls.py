from django.urls import path

from apps.payments import views

urlpatterns = [
    path("payments/create", views.PaymentCreateView.as_view()),
    path("payments/confirm", views.PaymentConfirmView.as_view()),
    path("payments/webhook/<str:provider>", views.PaymentWebhookView.as_view()),
]
