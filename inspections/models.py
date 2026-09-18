from django.conf import settings
from django.db import models

from products.models import Product, ProductInspectionItem


class BatchStatus(models.TextChoices):
    PENDING = "PENDING", "待檢驗"
    INSPECTING = "INSPECTING", "檢驗中"
    COMPLETED = "COMPLETED", "已完成"
    CANCELLED = "CANCELLED", "已取消"


class InspectionOverallResult(models.TextChoices):
    PASS = "PASS", "合格"
    FAIL = "FAIL", "不合格"
    PENDING = "PENDING", "待判定"


class InspectionItemResult(models.TextChoices):
    PASS = "PASS", "合格"
    FAIL = "FAIL", "不合格"
    PENDING = "PENDING", "待判定"
    NA = "NA", "不適用"


class InspectionBatch(models.Model):
    code = models.CharField(max_length=100, unique=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="batches")
    quantity = models.PositiveIntegerField()
    status = models.CharField(max_length=12, choices=BatchStatus.choices, default=BatchStatus.PENDING)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_batches")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inspection_batches"
        indexes = [
            models.Index(fields=["product", "status"]),
            models.Index(fields=["created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return self.code


class InspectionRecord(models.Model):
    batch = models.ForeignKey(InspectionBatch, on_delete=models.PROTECT, related_name="records")
    inspector = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="inspection_records")
    inspection_date = models.DateTimeField(auto_now_add=True)
    overall_result = models.CharField(
        max_length=8,
        choices=InspectionOverallResult.choices,
        default=InspectionOverallResult.PENDING,
    )
    remark = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inspection_records"
        indexes = [
            models.Index(fields=["batch"]),
            models.Index(fields=["inspector"]),
            models.Index(fields=["overall_result"]),
        ]
        ordering = ["-inspection_date"]

    def __str__(self):
        return f"{self.batch.code} #{self.pk}"


class InspectionResult(models.Model):
    inspection = models.ForeignKey(InspectionRecord, on_delete=models.CASCADE, related_name="results")
    product_inspection_item = models.ForeignKey(
        ProductInspectionItem,
        on_delete=models.PROTECT,
        related_name="results",
    )
    measured_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    measured_text = models.CharField(max_length=255, blank=True)
    result = models.CharField(max_length=8, choices=InspectionItemResult.choices, default=InspectionItemResult.PENDING)
    inspection_type_snapshot = models.CharField(max_length=16, blank=True)
    inspection_method_snapshot = models.CharField(max_length=100, blank=True)
    standard_min_snapshot = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    standard_max_snapshot = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    standard_value_snapshot = models.CharField(max_length=255, blank=True)
    remark = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inspection_results"
        constraints = [
            models.UniqueConstraint(
                fields=["inspection", "product_inspection_item"],
                name="uq_inspection_product_item",
            )
        ]
        indexes = [models.Index(fields=["result"])]
        ordering = ["product_inspection_item__sort_order", "id"]

    def save(self, *args, **kwargs):
        config = self.product_inspection_item
        if not self.inspection_type_snapshot:
            self.inspection_type_snapshot = config.inspection_type
        if not self.inspection_method_snapshot:
            self.inspection_method_snapshot = config.inspection_method
        if self.standard_min_snapshot is None:
            self.standard_min_snapshot = config.standard_min
        if self.standard_max_snapshot is None:
            self.standard_max_snapshot = config.standard_max
        if not self.standard_value_snapshot:
            self.standard_value_snapshot = config.standard_value
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.inspection_id} - {self.product_inspection_item_id}"
