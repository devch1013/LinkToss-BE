import uuid

from django.db import models

from api.deck.models import Deck
from api.user.models.user import User
from common.abstract_models.soft_delete_model import SoftDeleteModel
from common.abstract_models.time_stamp_model import TimeStampModel


class Drop(TimeStampModel, SoftDeleteModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="drops")
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name="drops")
    url = models.URLField()
    memo = models.TextField(blank=True, null=True)
    favicon_url = models.URLField(blank=True, null=True)
    screenshot_url = models.URLField(blank=True, null=True)
    meta_image_url = models.URLField(blank=True, null=True)

    class Meta:
        db_table = "drops"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["deck"]),
        ]

    def __str__(self):
        return self.title
