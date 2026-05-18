from django.contrib.auth import authenticate
from rest_framework import serializers

from apps.accounts.managers import UserManager
from apps.accounts.models import DeliveryPartnerProfile, User, UserRole, VendorProfile
from apps.accounts.services.otp import send_otp, verify_otp
from apps.accounts.models import OtpPurpose


class UserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "name", "email", "phone", "role", "avatar_url")
        read_only_fields = fields

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["id"] = str(data["id"])
        if data.get("avatar_url"):
            request = self.context.get("request")
            if request:
                data["avatarUrl"] = request.build_absolute_uri(data.pop("avatar_url"))
            else:
                data["avatarUrl"] = data.pop("avatar_url")
        else:
            data.pop("avatar_url", None)
        return data

    def get_avatar_url(self, obj):
        if obj.avatar:
            request = self.context.get("request")
            if request:
                return obj.avatar.url
            return obj.avatar.url
        return None


class SignupSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20)
    role = serializers.ChoiceField(choices=UserRole.choices)
    password = serializers.CharField(min_length=6, write_only=True, required=False)

    def validate_phone(self, value):
        return UserManager.normalize_phone(value)

    def validate_role(self, value):
        if value in (UserRole.STAFF, UserRole.ADMIN):
            raise serializers.ValidationError("This role cannot self-register.")
        return value

    def create(self, validated_data):
        phone = validated_data["phone"]
        if User.objects.filter(phone=phone).exists():
            raise serializers.ValidationError({"phone": "Phone already registered."})
        password = validated_data.pop("password", None)
        user = User.objects.create_user(
            phone=phone,
            password=password,
            name=validated_data["name"],
            email=validated_data["email"],
            role=validated_data["role"],
        )
        if user.role == UserRole.VENDOR:
            VendorProfile.objects.create(user=user, business_name=validated_data["name"])
            from apps.stores.models import Store

            Store.objects.create(
                owner=user.vendor_profile,
                name=f"{validated_data['name']}'s Store",
            )
        elif user.role == UserRole.DELIVERY_PARTNER:
            DeliveryPartnerProfile.objects.create(user=user)
        send_otp(phone, OtpPurpose.SIGNUP)
        return user


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)
    password = serializers.CharField(required=False, allow_blank=True, write_only=True)

    def validate_phone(self, value):
        return UserManager.normalize_phone(value)


class VerifyOtpSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)
    otp = serializers.CharField(min_length=6, max_length=6)

    def validate_phone(self, value):
        return UserManager.normalize_phone(value)


class PasswordResetRequestSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)

    def validate_phone(self, value):
        return UserManager.normalize_phone(value)


class PasswordResetConfirmSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)
    otp = serializers.CharField(min_length=6, max_length=6)
    new_password = serializers.CharField(min_length=6, write_only=True)

    def validate_phone(self, value):
        return UserManager.normalize_phone(value)


class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()

    def to_internal_value(self, data):
        if isinstance(data, dict):
            token = data.get("refreshToken") or data.get("refresh_token")
            if token is not None:
                return {"refresh_token": token}
        return super().to_internal_value(data)
