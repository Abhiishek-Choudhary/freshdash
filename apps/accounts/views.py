from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.exceptions import APIError
from apps.accounts.models import OtpChallenge, OtpPurpose, User
from apps.accounts.serializers import (
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RefreshTokenSerializer,
    SignupSerializer,
    UserSerializer,
    VerifyOtpSerializer,
)
from apps.accounts.services.otp import send_otp, verify_otp
from apps.accounts.services.tokens import build_auth_response


class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"otpSent": True})


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone"]
        password = serializer.validated_data.get("password")

        if password:
            user = User.objects.filter(phone=phone).first()
            if not user or not user.check_password(password):
                raise APIError("Invalid phone or password", code="invalid_credentials", status_code=401)
            return Response(build_auth_response(user))

        if not User.objects.filter(phone=phone).exists():
            raise APIError("User not found. Please sign up.", code="user_not_found", status_code=404)
        send_otp(phone, OtpPurpose.LOGIN)
        return Response({"otpSent": True})


class VerifyOtpView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone"]
        otp = serializer.validated_data["otp"]
        challenge = (
            OtpChallenge.objects.filter(phone=phone, consumed=False)
            .order_by("-created_at")
            .first()
        )
        if not challenge:
            raise APIError("Invalid or expired OTP", code="invalid_otp", status_code=400)
        verify_otp(phone, otp, challenge.purpose)
        user = User.objects.filter(phone=phone).first()
        if not user:
            raise APIError("User not found", code="user_not_found", status_code=404)
        return Response(build_auth_response(user))


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user, context={"request": request}).data)


class LogoutView(APIView):
    def post(self, request):
        refresh = request.data.get("refreshToken") or request.data.get("refresh_token")
        if refresh:
            try:
                RefreshToken(refresh).blacklist()
            except TokenError:
                pass
        return Response(status=status.HTTP_204_NO_CONTENT)


class RefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token_str = serializer.validated_data["refresh_token"]
        try:
            refresh = RefreshToken(token_str)
            return Response({"accessToken": str(refresh.access_token)})
        except TokenError as exc:
            raise APIError("Invalid refresh token", code="invalid_token", status_code=401) from exc


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone"]
        if not User.objects.filter(phone=phone).exists():
            raise APIError("User not found", code="user_not_found", status_code=404)
        send_otp(phone, OtpPurpose.RESET_PASSWORD)
        return Response({"otpSent": True})


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone"]
        verify_otp(phone, serializer.validated_data["otp"], OtpPurpose.RESET_PASSWORD)
        user = User.objects.get(phone=phone)
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        return Response({"success": True})


class PasswordLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone = request.data.get("phone")
        password = request.data.get("password")
        if not phone or not password:
            raise APIError("Phone and password required", code="validation_error")
        from apps.accounts.managers import UserManager

        phone = UserManager.normalize_phone(phone)
        user = authenticate(request, username=phone, password=password)
        if not user:
            user_obj = User.objects.filter(phone=phone).first()
            if user_obj and user_obj.check_password(password):
                user = user_obj
        if not user:
            raise APIError("Invalid credentials", code="invalid_credentials", status_code=401)
        return Response(build_auth_response(user))
