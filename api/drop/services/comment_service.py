from typing import Optional
from uuid import UUID

from django.db import transaction
from django.db.models import QuerySet

from api.drop.models.comment import Comment
from api.drop.models.drop import Drop
from api.user.models.user import User


class CommentService:
    @classmethod
    def get_drop_comments(cls, drop_id: UUID, user: User) -> QuerySet[Comment]:
        """특정 drop의 최상위 댓글 목록 조회 (parent가 None인 것들)"""
        return Comment.objects.filter(
            drop_id=drop_id,
            parent__isnull=True,
            deleted_at__isnull=True,
        ).select_related("user", "drop")

    @classmethod
    def get_comment_by_id(cls, comment_id: UUID) -> Optional[Comment]:
        """comment ID로 단일 조회"""
        try:
            return Comment.objects.select_related("user", "drop", "parent").get(
                id=comment_id, deleted_at__isnull=True
            )
        except Comment.DoesNotExist:
            return None

    @classmethod
    def get_comment_replies(cls, comment_id: UUID) -> QuerySet[Comment]:
        """특정 댓글의 대댓글 조회"""
        return Comment.objects.filter(
            parent_id=comment_id, deleted_at__isnull=True
        ).select_related("user", "drop")

    @classmethod
    @transaction.atomic
    def create_comment(
        cls,
        user: User,
        drop_id: UUID,
        content: str,
        parent_id: Optional[UUID] = None,
    ) -> Comment:
        """새로운 댓글 생성"""
        # drop 존재 확인
        try:
            drop = Drop.objects.get(id=drop_id, deleted_at__isnull=True)
        except Drop.DoesNotExist:
            raise ValueError(f"Drop with id {drop_id} not found")

        parent = None
        if parent_id:
            parent = cls._get_parent_comment(parent_id)
            # parent의 drop과 현재 drop이 일치하는지 확인
            if parent.drop_id != drop_id:
                raise ValueError("Parent comment does not belong to the same drop")

        comment = Comment.objects.create(
            user=user,
            drop=drop,
            content=content,
            parent=parent,
        )
        return comment

    @classmethod
    @transaction.atomic
    def update_comment(
        cls,
        comment_id: UUID,
        user: User,
        content: str,
    ) -> Optional[Comment]:
        """댓글 수정 (본인 댓글만)"""
        comment = cls.get_comment_by_id(comment_id)
        if not comment:
            return None

        # 본인 댓글인지 확인
        if comment.user_id != user.id:
            raise PermissionError("You can only edit your own comments")

        comment.content = content
        comment.save()
        return comment

    @classmethod
    @transaction.atomic
    def delete_comment(cls, comment_id: UUID, user: User) -> bool:
        """댓글 soft delete (본인 댓글만, 대댓글도 함께 삭제)"""
        comment = cls.get_comment_by_id(comment_id)
        if not comment:
            return False

        # 본인 댓글인지 확인
        if comment.user_id != user.id:
            raise PermissionError("You can only delete your own comments")

        cls._soft_delete_recursive(comment)
        return True

    @classmethod
    def get_comment_tree(cls, comment: Comment) -> QuerySet[Comment]:
        """댓글의 전체 대댓글 트리 조회 (재귀적)"""
        return Comment.objects.filter(
            parent=comment, deleted_at__isnull=True
        ).select_related("user", "drop")

    # Internal helper methods

    @classmethod
    def _get_parent_comment(cls, parent_id: UUID) -> Comment:
        """parent comment 조회 (검증 포함)"""
        parent = cls.get_comment_by_id(parent_id)
        if not parent:
            raise ValueError(f"Parent comment with id {parent_id} not found")
        return parent

    @classmethod
    def _soft_delete_recursive(cls, comment: Comment):
        """댓글과 하위 대댓글을 재귀적으로 soft delete"""
        replies = Comment.objects.filter(parent=comment, deleted_at__isnull=True)
        for reply in replies:
            cls._soft_delete_recursive(reply)

        comment.delete()  # SoftDeleteModel의 delete 사용
