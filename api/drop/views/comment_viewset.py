from uuid import UUID

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.drop.serializers import (
    CommentCreateSerializer,
    CommentSerializer,
    CommentTreeSerializer,
    CommentUpdateSerializer,
)
from api.drop.services.comment_service import CommentService


class CommentViewSet(viewsets.ViewSet):
    """Comment CRUD ViewSet"""

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Comment 목록 조회",
        operation_description="특정 drop의 최상위 댓글 목록을 조회합니다.",
        manual_parameters=[
            openapi.Parameter(
                "drop_id",
                openapi.IN_QUERY,
                description="Drop ID (required)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_UUID,
                required=True,
            )
        ],
        responses={200: CommentSerializer(many=True)},
    )
    def list(self, request):
        """Comment 목록 조회 (최상위 댓글만)"""
        drop_id = request.query_params.get("drop_id")

        if not drop_id:
            return Response(
                {"error": "drop_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            comments = CommentService.get_drop_comments(UUID(drop_id), request.user)
            serializer = CommentSerializer(comments, many=True)
            return Response(serializer.data)
        except ValueError:
            return Response(
                {"error": "Invalid drop_id format"}, status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        operation_summary="Comment 상세 조회",
        operation_description="특정 comment의 상세 정보를 조회합니다.",
        responses={200: CommentSerializer(), 404: "Comment not found"},
    )
    def retrieve(self, request, pk=None):
        """Comment 상세 조회"""
        try:
            comment = CommentService.get_comment_by_id(UUID(pk))
        except ValueError:
            return Response(
                {"error": "Invalid comment ID format"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not comment:
            return Response(
                {"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = CommentSerializer(comment)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Comment 생성",
        operation_description="새로운 댓글을 생성합니다. parent를 지정하면 대댓글이 됩니다.",
        request_body=CommentCreateSerializer,
        responses={201: CommentSerializer(), 400: "Bad request"},
    )
    def create(self, request):
        """Comment 생성"""
        serializer = CommentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            comment = CommentService.create_comment(
                user=request.user,
                drop_id=serializer.validated_data["drop"],
                content=serializer.validated_data["content"],
                parent_id=serializer.validated_data.get("parent"),
            )
            return Response(
                CommentSerializer(comment).data, status=status.HTTP_201_CREATED
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Comment 수정",
        operation_description="기존 댓글을 수정합니다. (본인 댓글만 가능)",
        request_body=CommentUpdateSerializer,
        responses={
            200: CommentSerializer(),
            400: "Bad request",
            403: "Permission denied",
            404: "Comment not found",
        },
    )
    def update(self, request, pk=None):
        """Comment 수정"""
        serializer = CommentUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            comment = CommentService.update_comment(
                comment_id=UUID(pk),
                user=request.user,
                content=serializer.validated_data["content"],
            )

            if not comment:
                return Response(
                    {"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND
                )

            return Response(CommentSerializer(comment).data)
        except PermissionError as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Comment 삭제",
        operation_description="댓글을 soft delete합니다. (본인 댓글만 가능, 대댓글도 함께 삭제)",
        responses={
            204: "Deleted successfully",
            403: "Permission denied",
            404: "Comment not found",
        },
    )
    def destroy(self, request, pk=None):
        """Comment 삭제"""
        try:
            success = CommentService.delete_comment(UUID(pk), request.user)

            if not success:
                return Response(
                    {"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND
                )

            return Response(status=status.HTTP_204_NO_CONTENT)
        except PermissionError as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValueError:
            return Response(
                {"error": "Invalid comment ID format"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @swagger_auto_schema(
        operation_summary="Comment 대댓글 조회",
        operation_description="특정 댓글의 대댓글 목록을 조회합니다.",
        responses={200: CommentSerializer(many=True)},
    )
    @action(detail=True, methods=["get"], url_path="replies")
    def replies(self, request, pk=None):
        """Comment의 대댓글 조회"""
        try:
            replies = CommentService.get_comment_replies(UUID(pk))
            serializer = CommentSerializer(replies, many=True)
            return Response(serializer.data)
        except ValueError:
            return Response(
                {"error": "Invalid comment ID format"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @swagger_auto_schema(
        operation_summary="Comment 트리 조회",
        operation_description="특정 drop의 전체 댓글 트리를 재귀적으로 조회합니다.",
        manual_parameters=[
            openapi.Parameter(
                "drop_id",
                openapi.IN_QUERY,
                description="Drop ID (required)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_UUID,
                required=True,
            )
        ],
        responses={200: CommentTreeSerializer(many=True)},
    )
    @action(detail=False, methods=["get"], url_path="tree")
    def tree(self, request):
        """Comment 트리 구조 조회"""
        drop_id = request.query_params.get("drop_id")

        if not drop_id:
            return Response(
                {"error": "drop_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            comments = CommentService.get_drop_comments(UUID(drop_id), request.user)
            serializer = CommentTreeSerializer(comments, many=True)
            return Response(serializer.data)
        except ValueError:
            return Response(
                {"error": "Invalid drop_id format"}, status=status.HTTP_400_BAD_REQUEST
            )
