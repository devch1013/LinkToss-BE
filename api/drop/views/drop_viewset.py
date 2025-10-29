from uuid import UUID

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.drop.serializers import (
    DropCreateSerializer,
    DropSerializer,
    DropUpdateSerializer,
)
from api.drop.services.drop_service import DropService


class DropViewSet(viewsets.ViewSet):
    """Drop CRUD ViewSet"""

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Drop 목록 조회",
        operation_description="특정 deck의 drop 목록을 조회합니다.",
        manual_parameters=[
            openapi.Parameter(
                "deck_id",
                openapi.IN_QUERY,
                description="Deck ID (required)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_UUID,
                required=True,
            )
        ],
        responses={200: DropSerializer(many=True)},
    )
    def list(self, request):
        """Drop 목록 조회"""
        deck_id = request.query_params.get("deck_id")

        if not deck_id:
            return Response(
                {"error": "deck_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            drops = DropService.get_deck_drops(UUID(deck_id), request.user)
            serializer = DropSerializer(drops, many=True)
            return Response(serializer.data)
        except ValueError:
            return Response(
                {"error": "Invalid deck_id format"}, status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        operation_summary="Drop 상세 조회",
        operation_description="특정 drop의 상세 정보를 조회합니다.",
        responses={200: DropSerializer(), 404: "Drop not found"},
    )
    def retrieve(self, request, pk=None):
        """Drop 상세 조회"""
        try:
            drop = DropService.get_drop_by_id(UUID(pk), request.user)
        except ValueError:
            return Response(
                {"error": "Invalid drop ID format"}, status=status.HTTP_400_BAD_REQUEST
            )

        if not drop:
            return Response(
                {"error": "Drop not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = DropSerializer(drop)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Drop 생성",
        operation_description="새로운 drop을 생성합니다. 태그도 함께 생성할 수 있습니다.",
        request_body=DropCreateSerializer,
        responses={201: DropSerializer(), 400: "Bad request"},
    )
    def create(self, request):
        """Drop 생성"""
        serializer = DropCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            drop = DropService.create_drop(
                user=request.user,
                deck_id=serializer.validated_data["deck"],
                title=serializer.validated_data["title"],
                url=serializer.validated_data["url"],
                content=serializer.validated_data.get("content"),
                memo=serializer.validated_data.get("memo"),
                tag_names=serializer.validated_data.get("tags", []),
            )
            return Response(DropSerializer(drop).data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Drop 수정",
        operation_description="기존 drop을 수정합니다. 태그도 업데이트할 수 있습니다.",
        request_body=DropUpdateSerializer,
        responses={200: DropSerializer(), 400: "Bad request", 404: "Drop not found"},
    )
    def update(self, request, pk=None):
        """Drop 수정"""
        serializer = DropUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            drop = DropService.update_drop(
                drop_id=UUID(pk),
                user=request.user,
                title=serializer.validated_data.get("title"),
                content=serializer.validated_data.get("content"),
                url=serializer.validated_data.get("url"),
                memo=serializer.validated_data.get("memo"),
                deck_id=serializer.validated_data.get("deck"),
                tag_names=serializer.validated_data.get("tags"),
            )

            if not drop:
                return Response(
                    {"error": "Drop not found"}, status=status.HTTP_404_NOT_FOUND
                )

            return Response(DropSerializer(drop).data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Drop 삭제",
        operation_description="drop을 soft delete합니다.",
        responses={204: "Deleted successfully", 404: "Drop not found"},
    )
    def destroy(self, request, pk=None):
        """Drop 삭제"""
        try:
            success = DropService.delete_drop(UUID(pk), request.user)
        except ValueError:
            return Response(
                {"error": "Invalid drop ID format"}, status=status.HTTP_400_BAD_REQUEST
            )

        if not success:
            return Response(
                {"error": "Drop not found"}, status=status.HTTP_404_NOT_FOUND
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        operation_summary="Drop 검색",
        operation_description="제목, 내용, 메모, 태그로 drop을 검색합니다.",
        manual_parameters=[
            openapi.Parameter(
                "query",
                openapi.IN_QUERY,
                description="Search query",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "tags",
                openapi.IN_QUERY,
                description="Tag names (comma-separated)",
                type=openapi.TYPE_STRING,
            ),
        ],
        responses={200: DropSerializer(many=True)},
    )
    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request):
        """Drop 검색"""
        query = request.query_params.get("query")
        tags_param = request.query_params.get("tags")

        tag_names = None
        if tags_param:
            tag_names = [tag.strip() for tag in tags_param.split(",") if tag.strip()]

        drops = DropService.search_drops(request.user, query, tag_names)
        serializer = DropSerializer(drops, many=True)
        return Response(serializer.data)
