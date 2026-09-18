from django.conf import settings
from django.db import models

from defects.models import DefectRecord


class CorrectiveActionStatus(models.TextChoices):
    PENDING = "PENDING", "待處理"
    PROCESSING = "PROCESSING", "處理中"
    COMPLETED = "COMPLETED", "已完成"
    CANCELLED = "CANCELLED", "已取消"


class CorrectiveAction(models.Model):
    defect = models.ForeignKey(DefectRecord, on_delete=models.PROTECT, related_name="corrective_actions")
    action_description = models.TextField()
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_actions",
    )
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=CorrectiveActionStatus.choices, default=CorrectiveActionStatus.PENDING)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "corrective_actions"
        indexes = [models.Index(fields=["status", "due_date"])]
        ordering = ["due_date", "id"]

    def __str__(self):
        return f"CA-{self.pk or 'new'}"
