from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.serializers import UserSerializer


def build_auth_response(user):
    refresh = RefreshToken.for_user(user)
    return {
        "user": UserSerializer(user, context={"request": None}).data,
        "tokens": {
            "accessToken": str(refresh.access_token),
            "refreshToken": str(refresh),
        },
    }
