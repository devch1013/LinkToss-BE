import uuid

from django.db import models

from api.user.models.user import User
from common.abstract_models.soft_delete_model import SoftDeleteModel
from common.abstract_models.time_stamp_model import TimeStampModel


class Deck(TimeStampModel, SoftDeleteModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="decks")
    color_hex = models.CharField(max_length=7, default="#000000")
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    order = models.IntegerField(default=0)
    is_public = models.BooleanField(default=False)

    class Meta:
        db_table = "decks"
        ordering = ["order", "created_at"]
        indexes = [
            models.Index(fields=["user", "parent"]),
            models.Index(fields=["parent"]),
        ]

    def __str__(self):
        return self.name

    @property
    def depth(self):
        """현재 deck의 깊이 반환"""
        depth = 0
        current = self.parent
        while current:
            depth += 1
            current = current.parent
        return depth

    def get_ancestors(self):
        """상위 deck 리스트 반환 (root부터)"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.insert(0, current)
            current = current.parent
        return ancestors

    def get_root(self):
        """최상위 root deck 반환"""
        current = self
        while current.parent:
            current = current.parent
        return current
