from django.db import models

from common.abstract_models.soft_delete_model import SoftDeleteModel
from common.abstract_models.time_stamp_model import TimeStampModel


class Tag(TimeStampModel, SoftDeleteModel):
    name = models.CharField(max_length=255)
