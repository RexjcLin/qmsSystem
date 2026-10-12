from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _, pgettext_lazy
from products.models import Product, ProductInspectionItem


class BatchStatus(models.TextChoices):
    PENDING = "PENDING", pgettext_lazy("inspection batch status", "Pending")
    INSPECTING = "INSPECTING", pgettext_lazy("inspection batch status", "In progress")
    COMPLETED = "COMPLETED", _("Completed")
    CANCELLED = "CANCELLED", _("Cancelled")


class InspectionBatch(models.Model):
    code = models.CharField(max_length=100, unique=True, verbose_name=_("Batch code"))
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="batches", verbose_name=_("Product"))
    quantity = models.PositiveIntegerField(verbose_name=_("Quantity"))
    status = models.CharField(max_length=12, choices=BatchStatus.choices, default=BatchStatus.PENDING, verbose_name=_("Status"))
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_batches", verbose_name=_("Created by"))
    assigned_inspector = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="claimed_batches", verbose_name=_("Assigned inspector"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))
    class Meta:
        db_table = "inspection_batches"
        indexes = [models.Index(fields=["status"]), models.Index(fields=["created_at"])]
        verbose_name = _("Inspection batch")
        verbose_name_plural = _("Inspection batches")
    def __str__(self): return self.code


class ResultStatus(models.TextChoices):
    PASS = "PASS", _("Pass")
    FAIL = "FAIL", _("Fail")
    PENDING = "PENDING", pgettext_lazy("inspection result status", "Pending")
    NA = "NA", _("N/A")


class InspectionRecord(models.Model):
    batch = models.ForeignKey(InspectionBatch, on_delete=models.PROTECT, related_name="records", verbose_name=_("Inspection batch"))
    inspector = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="inspection_records", verbose_name=_("Inspector"))
    inspection_date = models.DateTimeField(auto_now_add=True, verbose_name=_("Inspection date"))
    overall_result = models.CharField(max_length=8, choices=ResultStatus.choices, default=ResultStatus.PENDING, verbose_name=_("Overall result"))
    remark = models.TextField(blank=True, verbose_name=_("Remark"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    class Meta:
        db_table = "inspection_records"
        verbose_name = _("Inspection record")
        verbose_name_plural = _("Inspection records")


class InspectionResult(models.Model):
    inspection = models.ForeignKey(InspectionRecord, on_delete=models.CASCADE, related_name="results", verbose_name=_("Inspection record"))
    product_item = models.ForeignKey(ProductInspectionItem, on_delete=models.PROTECT, related_name="results", verbose_name=_("Product inspection item"))
    measured_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name=_("Measured value"))
    result = models.CharField(max_length=8, choices=ResultStatus.choices, verbose_name=_("Result"))
    standard_min_snapshot = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name=_("Standard minimum snapshot"))
    standard_max_snapshot = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name=_("Standard maximum snapshot"))
    inspection_method_snapshot = models.CharField(max_length=100, blank=True, verbose_name=_("Inspection method snapshot"))
    unit_snapshot = models.CharField(max_length=30, blank=True, verbose_name=_("Unit snapshot"))
    remark = models.TextField(blank=True, verbose_name=_("Remark"))
    class Meta:
        db_table = "inspection_results"
        constraints = [models.UniqueConstraint(fields=["inspection", "product_item"], name="uq_inspection_product_item")]
        verbose_name = _("Inspection result")
        verbose_name_plural = _("Inspection results")
