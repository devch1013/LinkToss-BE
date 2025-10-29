from rest_framework import serializers

from api.user.models import User


class UserSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(required=False)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "phone_number",
            "profile_image",
            "provider",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "provider", "created_at", "updated_at"]


class UserProfileUpdateSerializer(serializers.Serializer):
    """사용자 프로필 수정용 Serializer"""

    username = serializers.CharField(max_length=255, required=False)
    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(max_length=20, required=False)
    profile_image = serializers.ImageField(required=False)


class UserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "profile_image"]


class TokenSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=True)
    access_token = serializers.CharField(required=True)
    refresh_token = serializers.CharField(required=True)
    token_type = serializers.CharField(required=True)


class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=True)


# 소셜 로그인용 Serializer들
class SocialLoginRequestSerializer(serializers.Serializer):
    """소셜 로그인 요청 데이터"""

    identifier = serializers.CharField(
        required=False, help_text="사용자 ID (native 로그인)"
    )
    password = serializers.CharField(
        required=False, write_only=True, help_text="비밀번호 (native 로그인)"
    )
    id_token = serializers.CharField(
        required=False, help_text="Firebase ID Token (Firebase 로그인)"
    )


class SocialLoginQuerySerializer(serializers.Serializer):
    """소셜 로그인 쿼리 파라미터"""

    code = serializers.CharField(
        required=False, help_text="OAuth 인증 코드 (소셜 로그인 시 필요)"
    )


class MessageResponseSerializer(serializers.Serializer):
    """일반적인 메시지 응답"""

    message = serializers.CharField(help_text="응답 메시지")
