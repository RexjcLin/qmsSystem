from django.conf import settings
from django.db import models
from inspections.models import InspectionRecord


class DefectType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=10, choices=[("ACTIVE", "啟用"), ("INACTIVE", "停用")], default="ACTIVE")
    class Meta: db_table = "defect_types"
    def __str__(self): return self.name


class DefectRecord(models.Model):
    class Status(models.TextChoices):
        NEW = "NEW", "新建"
        CONFIRMED = "CONFIRMED", "已確認"
        PROCESSING = "PROCESSING", "處理中"
        RESOLVED = "RESOLVED", "已改善"
        CLOSED = "CLOSED", "結案"
    inspection = models.ForeignKey(InspectionRecord, on_delete=models.PROTECT, related_name="defects")
    defect_type = models.ForeignKey(DefectType, on_delete=models.PROTECT, related_name="records")
    description = models.TextField(blank=True)
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reported_defects")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = "defect_records"


class DefectImage(models.Model):
    defect = models.ForeignKey(DefectRecord, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="defects/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = "defect_images"


class CorrectiveAction(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "待處理"
        PROCESSING = "PROCESSING", "處理中"
        COMPLETED = "COMPLETED", "已完成"
        CANCELLED = "CANCELLED", "已取消"
    defect = models.ForeignKey(DefectRecord, on_delete=models.PROTECT, related_name="corrective_actions")
    action_description = models.TextField()
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_actions")
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = "corrective_actions"
