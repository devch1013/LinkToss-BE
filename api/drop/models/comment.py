import uuid

from django.db import models

from api.drop.models.drop import Drop
from api.user.models.user import User
from common.abstract_models.soft_delete_model import SoftDeleteModel
from common.abstract_models.time_stamp_model import TimeStampModel


class Comment(TimeStampModel, SoftDeleteModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    drop = models.ForeignKey(Drop, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, related_name="replies", null=True, blank=True
    )
    content = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "comments"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["drop", "parent"]),
        ]

    def __str__(self):
        return f"Comment by {self.user.username} on {self.drop.title}"
