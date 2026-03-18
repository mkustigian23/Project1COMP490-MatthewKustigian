from django.db import models

# Create your models here.
class TimestampModel(models.Model):
    """
    A base abstract model that provides the creation and last update times of a model instance.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True