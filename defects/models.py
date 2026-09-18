from django.conf import settings
from django.db import models

from inspections.models import InspectionRecord


class DefectTypeStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "啟用"
    INACTIVE = "INACTIVE", "停用"


class DefectStatus(models.TextChoices):
    NEW = "NEW", "新建"
    CONFIRMED = "CONFIRMED", "已確認"
    PROCESSING = "PROCESSING", "處理中"
    RESOLVED = "RESOLVED", "已改善"
    CLOSED = "CLOSED", "結案"


class DefectType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=10, choices=DefectTypeStatus.choices, default=DefectTypeStatus.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "defect_types"
        ordering = ["name"]

    def __str__(self):
        return self.name


class DefectRecord(models.Model):
    inspection = models.ForeignKey(InspectionRecord, on_delete=models.PROTECT, related_name="defects")
    defect_type = models.ForeignKey(DefectType, on_delete=models.PROTECT, related_name="records")
    description = models.TextField(blank=True)
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reported_defects")
    status = models.CharField(max_length=12, choices=DefectStatus.choices, default=DefectStatus.NEW)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "defect_records"
        indexes = [
            models.Index(fields=["inspection", "status"]),
            models.Index(fields=["defect_type"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.defect_type.name} #{self.pk}"


class DefectImage(models.Model):
    defect = models.ForeignKey(DefectRecord, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="defects/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "defect_images"
        ordering = ["-uploaded_at"]
