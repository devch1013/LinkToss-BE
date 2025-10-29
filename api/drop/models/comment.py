from django.db import models

from api.drop.models.drop import Drop
from api.user.models.user import User
from common.abstract_models.soft_delete_model import SoftDeleteModel
from common.abstract_models.time_stamp_model import TimeStampModel


class Comment(TimeStampModel, SoftDeleteModel):
    drop = models.ForeignKey(Drop, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, related_name="replies", null=True, blank=True
    )
    content = models.TextField(blank=True, null=True)
