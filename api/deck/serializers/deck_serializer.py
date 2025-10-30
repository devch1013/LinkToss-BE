from rest_framework import serializers

from api.deck.models.deck import Deck
from api.drop.serializers.drop_serializer import DropSerializer
from common.serializers.breadcrumb_serializer import BreadcrumbSerializer


class DeckSerializer(serializers.ModelSerializer):
    """Deck 조회용 Serializer"""

    depth = serializers.IntegerField(read_only=True)
    children_count = serializers.SerializerMethodField()

    class Meta:
        model = Deck
        fields = [
            "id",
            "name",
            "description",
            "color_hex",
            "parent",
            "order",
            "is_public",
            "depth",
            "children_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_children_count(self, obj):
        """하위 children 개수"""
        return obj.children.filter(is_deleted=False).count()


class DeckCreateSerializer(serializers.ModelSerializer):
    """Deck 생성용 Serializer"""

    class Meta:
        model = Deck
        fields = [
            "name",
            "description",
            "color_hex",
            "parent",
            "is_public",
        ]

    def validate_color_hex(self, value):
        """color_hex 형식 검증"""
        if not value.startswith("#") or len(value) != 7:
            raise serializers.ValidationError(
                "Invalid color format. Use #RRGGBB format."
            )
        return value


class DeckUpdateSerializer(serializers.ModelSerializer):
    """Deck 수정용 Serializer"""

    class Meta:
        model = Deck
        fields = [
            "name",
            "description",
            "color_hex",
            "parent",
            "order",
            "is_public",
        ]
        extra_kwargs = {
            "name": {"required": False},
            "description": {"required": False},
            "color_hex": {"required": False},
            "parent": {"required": False},
            "order": {"required": False},
            "is_public": {"required": False},
        }

    def validate_color_hex(self, value):
        """color_hex 형식 검증"""
        if value and (not value.startswith("#") or len(value) != 7):
            raise serializers.ValidationError(
                "Invalid color format. Use #RRGGBB format."
            )
        return value

    def validate_parent(self, value):
        """parent 순환 참조 검증"""
        if value and self.instance:
            if value.id == self.instance.id:
                raise serializers.ValidationError("Deck cannot be its own parent")
        return value


class DeckTreeSerializer(serializers.ModelSerializer):
    """Deck 트리 구조 조회용 Serializer (재귀적으로 children 포함)"""

    children = serializers.SerializerMethodField()
    depth = serializers.IntegerField(read_only=True)

    class Meta:
        model = Deck
        fields = [
            "id",
            "name",
            "description",
            "color_hex",
            "order",
            "is_public",
            "depth",
            "children",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_children(self, obj):
        """재귀적으로 children 조회"""
        children = obj.children.filter(is_deleted=False).order_by("order")
        return DeckTreeSerializer(children, many=True).data


class DeckDetailSerializer(serializers.ModelSerializer):
    """Deck 상세 조회용 Serializer (sub-deck과 drops 포함)"""

    depth = serializers.IntegerField(read_only=True)
    children_count = serializers.SerializerMethodField()
    breadcrumb = BreadcrumbSerializer(many=True, read_only=True)
    children = DeckSerializer(many=True, read_only=True)
    drops = DropSerializer(many=True, read_only=True)

    class Meta:
        model = Deck
        fields = [
            "id",
            "name",
            "description",
            "color_hex",
            "parent",
            "order",
            "is_public",
            "depth",
            "children_count",
            "breadcrumb",
            "children",
            "drops",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_children_count(self, obj):
        """하위 children 개수"""
        return obj.children.filter(is_deleted=False).count()
