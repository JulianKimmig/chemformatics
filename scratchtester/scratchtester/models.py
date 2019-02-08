from django.db import models
from django.contrib.postgres.fields import JSONField


class CsvStructure(models.Model):
    name = models.fields.CharField(max_length=20)
    html = models.fields.CharField(max_length=255, null=True)


class Measurement(models.Model):
    name = models.fields.CharField(max_length=20, default="new_measurment")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    raw_data = models.fields.FilePathField(default=None, null=True)
    raw_structure = models.ForeignKey(
        CsvStructure,
        on_delete=models.SET_DEFAULT,
        default=CsvStructure.objects.get_or_create(name="YZYZ")[0],
    )
    options = models.fields.CharField(max_length=400, default="{}")
