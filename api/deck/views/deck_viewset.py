from uuid import UUID

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.deck.serializers import (
    DeckCreateSerializer,
    DeckSerializer,
    DeckTreeSerializer,
    DeckUpdateSerializer,
)
from api.deck.services.deck_service import DeckService


class DeckViewSet(viewsets.ViewSet):
    """Deck CRUD ViewSet"""

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Deck 목록 조회",
        operation_description="사용자의 deck 목록을 조회합니다. parent 파라미터로 특정 deck의 children만 조회 가능합니다.",
        manual_parameters=[
            openapi.Parameter(
                "parent",
                openapi.IN_QUERY,
                description="Parent deck ID (optional)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_UUID,
            )
        ],
        responses={200: DeckSerializer(many=True)},
    )
    def list(self, request):
        """Deck 목록 조회"""
        parent_id = request.query_params.get("parent")
        parent = None

        if parent_id:
            try:
                parent = DeckService.get_deck_by_id(UUID(parent_id), request.user)
                if not parent:
                    return Response(
                        {"error": "Parent deck not found"},
                        status=status.HTTP_404_NOT_FOUND,
                    )
            except ValueError:
                return Response(
                    {"error": "Invalid parent ID format"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        decks = DeckService.get_user_decks(request.user, parent)
        serializer = DeckSerializer(decks, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Deck 상세 조회",
        operation_description="특정 deck의 상세 정보를 조회합니다.",
        responses={200: DeckSerializer(), 404: "Deck not found"},
    )
    def retrieve(self, request, pk=None):
        """Deck 상세 조회"""
        try:
            deck = DeckService.get_deck_by_id(UUID(pk), request.user)
        except ValueError:
            return Response(
                {"error": "Invalid deck ID format"}, status=status.HTTP_400_BAD_REQUEST
            )

        if not deck:
            return Response(
                {"error": "Deck not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = DeckSerializer(deck)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Deck 생성",
        operation_description="새로운 deck을 생성합니다.",
        request_body=DeckCreateSerializer,
        responses={201: DeckSerializer(), 400: "Bad request"},
    )
    def create(self, request):
        """Deck 생성"""
        serializer = DeckCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            deck = DeckService.create_deck(
                user=request.user,
                name=serializer.validated_data["name"],
                description=serializer.validated_data.get("description"),
                color_hex=serializer.validated_data.get("color_hex", "#000000"),
                parent_id=serializer.validated_data.get("parent").id
                if serializer.validated_data.get("parent")
                else None,
                is_public=serializer.validated_data.get("is_public", False),
            )
            return Response(DeckSerializer(deck).data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Deck 수정",
        operation_description="기존 deck을 수정합니다.",
        request_body=DeckUpdateSerializer,
        responses={200: DeckSerializer(), 400: "Bad request", 404: "Deck not found"},
    )
    def update(self, request, pk=None):
        """Deck 수정"""
        serializer = DeckUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            deck = DeckService.update_deck(
                deck_id=UUID(pk),
                user=request.user,
                name=serializer.validated_data.get("name"),
                description=serializer.validated_data.get("description"),
                color_hex=serializer.validated_data.get("color_hex"),
                parent_id=serializer.validated_data.get("parent").id
                if serializer.validated_data.get("parent")
                else None,
                order=serializer.validated_data.get("order"),
                is_public=serializer.validated_data.get("is_public"),
            )

            if not deck:
                return Response(
                    {"error": "Deck not found"}, status=status.HTTP_404_NOT_FOUND
                )

            return Response(DeckSerializer(deck).data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Deck 삭제",
        operation_description="deck을 soft delete합니다. 하위 children도 함께 삭제됩니다.",
        responses={204: "Deleted successfully", 404: "Deck not found"},
    )
    def destroy(self, request, pk=None):
        """Deck 삭제"""
        try:
            success = DeckService.delete_deck(UUID(pk), request.user)
        except ValueError:
            return Response(
                {"error": "Invalid deck ID format"}, status=status.HTTP_400_BAD_REQUEST
            )

        if not success:
            return Response(
                {"error": "Deck not found"}, status=status.HTTP_404_NOT_FOUND
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        operation_summary="Deck 트리 조회",
        operation_description="Deck의 전체 트리 구조를 재귀적으로 조회합니다.",
        manual_parameters=[
            openapi.Parameter(
                "deck_id",
                openapi.IN_QUERY,
                description="Root deck ID (optional, 없으면 최상위부터)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_UUID,
            )
        ],
        responses={200: DeckTreeSerializer(many=True)},
    )
    @action(detail=False, methods=["get"], url_path="tree")
    def tree(self, request):
        """Deck 트리 구조 조회"""
        deck_id = request.query_params.get("deck_id")

        try:
            if deck_id:
                decks = DeckService.get_deck_tree(request.user, UUID(deck_id))
            else:
                decks = DeckService.get_deck_tree(request.user)

            serializer = DeckTreeSerializer(decks, many=True)
            return Response(serializer.data)
        except ValueError:
            return Response(
                {"error": "Invalid deck ID format"}, status=status.HTTP_400_BAD_REQUEST
            )
