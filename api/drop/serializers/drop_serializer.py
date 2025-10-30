from rest_framework import serializers

from api.drop.models.drop import Drop
from common.serializers.breadcrumb_serializer import BreadcrumbSerializer


class DropSerializer(serializers.ModelSerializer):
    """Drop 조회용 Serializer"""

    tags = serializers.SerializerMethodField()

    class Meta:
        model = Drop
        fields = [
            "id",
            "title",
            "content",
            "url",
            "memo",
            "deck",
            "tags",
            "favicon_url",
            "screenshot_url",
            "meta_image_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_tags(self, obj):
        """Drop에 연결된 태그 이름 목록"""
        return list(
            obj.tag_drop_mappings.filter(tag__is_deleted=False).values_list(
                "tag__name", flat=True
            )
        )


class DropDetailSerializer(serializers.ModelSerializer):
    tags = serializers.SerializerMethodField()
    breadcrumb = BreadcrumbSerializer(many=True, read_only=True)

    class Meta:
        model = Drop
        fields = [
            "id",
            "title",
            "content",
            "url",
            "memo",
            "deck",
            "tags",
            "favicon_url",
            "screenshot_url",
            "meta_image_url",
            "breadcrumb",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_tags(self, obj):
        """Drop에 연결된 태그 이름 목록"""
        return list(
            obj.tag_drop_mappings.filter(tag__is_deleted=False).values_list(
                "tag__name", flat=True
            )
        )


class DropCreateSerializer(serializers.Serializer):
    """Drop 생성용 Serializer"""

    title = serializers.CharField(max_length=255)
    content = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    url = serializers.URLField()
    memo = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    deck = serializers.UUIDField()
    tags = serializers.ListField(
        child=serializers.CharField(max_length=255),
        required=False,
        allow_empty=True,
    )


class DropUpdateSerializer(serializers.Serializer):
    """Drop 수정용 Serializer"""

    title = serializers.CharField(max_length=255, required=False)
    content = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    url = serializers.URLField(required=False)
    memo = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    deck = serializers.UUIDField(required=False)
    tags = serializers.ListField(
        child=serializers.CharField(max_length=255),
        required=False,
        allow_empty=True,
    )
