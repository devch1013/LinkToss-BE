from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.user.serializers.user_serializers import (
    UserProfileUpdateSerializer,
    UserSerializer,
)
from api.user.services.user_profile_service import UserProfileService


class UserProfileViewSet(viewsets.ViewSet):
    """User Profile ViewSet"""

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="내 프로필 조회",
        operation_description="현재 로그인한 사용자의 프로필 정보를 조회합니다.",
        responses={200: UserSerializer()},
    )
    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        """내 프로필 조회"""
        user = UserProfileService.get_user_profile(request.user)
        serializer = UserSerializer(user)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="내 프로필 수정",
        operation_description="현재 로그인한 사용자의 프로필 정보를 수정합니다. profile_image는 S3에 업로드됩니다.",
        request_body=UserProfileUpdateSerializer,
        responses={200: UserSerializer(), 400: "Bad request"},
    )
    @action(detail=False, methods=["patch"], url_path="me/update")
    def update_me(self, request):
        """내 프로필 수정"""
        serializer = UserProfileUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = UserProfileService.update_user_profile(
                user=request.user,
                username=serializer.validated_data.get("username"),
                email=serializer.validated_data.get("email"),
                phone_number=serializer.validated_data.get("phone_number"),
                profile_image=serializer.validated_data.get("profile_image"),
            )
            return Response(UserSerializer(user).data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
