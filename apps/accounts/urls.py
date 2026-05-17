from django.urls import path

from apps.accounts import views

urlpatterns = [
    path("signup", views.SignupView.as_view()),
    path("login", views.LoginView.as_view()),
    path("verify-otp", views.VerifyOtpView.as_view()),
    path("login/password", views.PasswordLoginView.as_view()),
    path("refresh", views.RefreshView.as_view()),
    path("logout", views.LogoutView.as_view()),
    path("me", views.MeView.as_view()),
    path("password/reset/request", views.PasswordResetRequestView.as_view()),
    path("password/reset/confirm", views.PasswordResetConfirmView.as_view()),
]
