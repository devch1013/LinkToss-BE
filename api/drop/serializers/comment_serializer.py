from rest_framework import serializers

from api.drop.models.comment import Comment


class CommentSerializer(serializers.ModelSerializer):
    """Comment 조회용 Serializer"""

    user_name = serializers.CharField(source="user.username", read_only=True)
    replies_count = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "content",
            "user",
            "user_name",
            "drop",
            "parent",
            "replies_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]

    def get_replies_count(self, obj):
        """대댓글 개수"""
        return obj.replies.filter(is_deleted=False).count()


class CommentCreateSerializer(serializers.Serializer):
    """Comment 생성용 Serializer"""

    drop = serializers.UUIDField()
    content = serializers.CharField()
    parent = serializers.UUIDField(required=False, allow_null=True)


class CommentUpdateSerializer(serializers.Serializer):
    """Comment 수정용 Serializer"""

    content = serializers.CharField()


class CommentTreeSerializer(serializers.ModelSerializer):
    """Comment 트리 구조 조회용 Serializer (재귀적으로 replies 포함)"""

    user_name = serializers.CharField(source="user.username", read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "content",
            "user",
            "user_name",
            "drop",
            "parent",
            "replies",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]

    def get_replies(self, obj):
        """재귀적으로 replies 조회"""
        replies = obj.replies.filter(is_deleted=False).order_by("created_at")
        return CommentTreeSerializer(replies, many=True).data
