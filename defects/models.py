from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _, pgettext_lazy
from inspections.models import InspectionRecord


class DefectType(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Defect type name"))
    description = models.CharField(max_length=255, blank=True, verbose_name=_("Description"))
    status = models.CharField(max_length=10, choices=[("ACTIVE", _("Active")), ("INACTIVE", _("Inactive"))], default="ACTIVE", verbose_name=_("Status"))
    class Meta:
        db_table = "defect_types"
        verbose_name = _("Defect type")
        verbose_name_plural = _("Defect types")
    def __str__(self): return self.name


class DefectRecord(models.Model):
    class Status(models.TextChoices):
        NEW = "NEW", _("New")
        CONFIRMED = "CONFIRMED", _("Confirmed")
        PROCESSING = "PROCESSING", pgettext_lazy("defect status", "In progress")
        RESOLVED = "RESOLVED", _("Resolved")
        CLOSED = "CLOSED", _("Closed")
    inspection = models.ForeignKey(InspectionRecord, on_delete=models.PROTECT, related_name="defects", verbose_name=_("Inspection record"))
    defect_type = models.ForeignKey(DefectType, on_delete=models.PROTECT, related_name="records", verbose_name=_("Defect type"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reported_defects", verbose_name=_("Reported by"))
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.NEW, verbose_name=_("Status"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    class Meta:
        db_table = "defect_records"
        verbose_name = _("Defect record")
        verbose_name_plural = _("Defect records")


class DefectImage(models.Model):
    defect = models.ForeignKey(DefectRecord, on_delete=models.CASCADE, related_name="images", verbose_name=_("Defect record"))
    image = models.ImageField(upload_to="defects/%Y/%m/", verbose_name=_("Image"))
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Uploaded at"))
    class Meta:
        db_table = "defect_images"
        verbose_name = _("Defect image")
        verbose_name_plural = _("Defect images")


class CorrectiveAction(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", pgettext_lazy("corrective action status", "Pending")
        PROCESSING = "PROCESSING", pgettext_lazy("corrective action status", "In progress")
        COMPLETED = "COMPLETED", _("Completed")
        CANCELLED = "CANCELLED", _("Cancelled")
    defect = models.ForeignKey(DefectRecord, on_delete=models.PROTECT, related_name="corrective_actions", verbose_name=_("Defect record"))
    action_description = models.TextField(verbose_name=_("Corrective action description"))
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_actions", verbose_name=_("Assigned to"))
    due_date = models.DateField(null=True, blank=True, verbose_name=_("Due date"))
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING, verbose_name=_("Status"))
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Completed at"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    class Meta:
        db_table = "corrective_actions"
        verbose_name = _("Corrective action")
        verbose_name_plural = _("Corrective actions")
