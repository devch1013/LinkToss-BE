import uuid

from django.db import models

from api.drop.models.drop import Drop
from common.abstract_models.soft_delete_model import SoftDeleteModel
from common.abstract_models.time_stamp_model import TimeStampModel


class Tag(TimeStampModel, SoftDeleteModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = "tags"
        ordering = ["name"]

    def __str__(self):
        return self.name


class TagDropMapping(TimeStampModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tag = models.ForeignKey(
        Tag, on_delete=models.CASCADE, related_name="tag_drop_mappings"
    )
    drop = models.ForeignKey(
        Drop, on_delete=models.CASCADE, related_name="tag_drop_mappings"
    )

    class Meta:
        db_table = "tag_drop_mappings"
        unique_together = [["tag", "drop"]]
        indexes = [
            models.Index(fields=["tag", "drop"]),
        ]

    def __str__(self):
        return f"{self.tag.name} - {self.drop.title}"
