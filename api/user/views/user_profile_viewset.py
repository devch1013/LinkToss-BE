from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.drop.serializers import DropSerializer
from api.drop.services.drop_service import DropService
from api.user.serializers.dashboard_serializer import DashboardSerializer
from api.user.serializers.user_serializers import (
    UserProfileUpdateSerializer,
    UserSerializer,
)
from api.user.services.dashboard_service import DashboardService
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

    @swagger_auto_schema(
        operation_summary="대시보드 조회",
        operation_description="사용자의 대시보드 정보를 조회합니다. (통계, 최근 drop 10개, 최근 조회 deck 5개)",
        responses={200: DashboardSerializer()},
    )
    @action(detail=False, methods=["get"], url_path="dashboard")
    def dashboard(self, request):
        """대시보드 조회"""
        dashboard_data = DashboardService.get_user_dashboard(request.user)
        serializer = DashboardSerializer(dashboard_data)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="최근 Drop 조회",
        operation_description="사용자가 저장한 최근 drop들을 시간순으로 조회합니다.",
        manual_parameters=[
            openapi.Parameter(
                "limit",
                openapi.IN_QUERY,
                description="조회할 drop 개수 (기본값: 10)",
                type=openapi.TYPE_INTEGER,
                default=10,
            )
        ],
        responses={200: DropSerializer(many=True)},
    )
    @action(detail=False, methods=["get"], url_path="recent-drops")
    def recent_drops(self, request):
        """최근 Drop 조회"""
        limit = request.query_params.get("limit", 10)

        try:
            limit = int(limit)
            if limit <= 0:
                return Response(
                    {"error": "limit must be a positive integer"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # 최대 100개로 제한
            limit = min(limit, 100)
        except ValueError:
            return Response(
                {"error": "Invalid limit parameter"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        recent_drops = DropService.get_recent_drops(request.user, limit)
        serializer = DropSerializer(recent_drops, many=True)
        return Response(serializer.data)
