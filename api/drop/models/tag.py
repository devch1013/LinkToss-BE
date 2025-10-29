from django.db import models

from api.drop.models.drop import Drop
from common.abstract_models.soft_delete_model import SoftDeleteModel
from common.abstract_models.time_stamp_model import TimeStampModel


class Tag(TimeStampModel, SoftDeleteModel):
    name = models.CharField(max_length=255)


class TagDropMapping(TimeStampModel):
    tag = models.ForeignKey(
        Tag, on_delete=models.CASCADE, related_name="tag_drop_mappings"
    )
    drop = models.ForeignKey(
        Drop, on_delete=models.CASCADE, related_name="tag_drop_mappings"
    )
