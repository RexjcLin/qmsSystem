from django.conf import settings
from django.db import models
from products.models import Product, ProductInspectionItem


class BatchStatus(models.TextChoices):
    PENDING = "PENDING", "待檢驗"
    INSPECTING = "INSPECTING", "檢驗中"
    COMPLETED = "COMPLETED", "已完成"
    CANCELLED = "CANCELLED", "已取消"


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
        indexes = [models.Index(fields=["status"]), models.Index(fields=["created_at"])]
    def __str__(self): return self.code


class ResultStatus(models.TextChoices):
    PASS = "PASS", "合格"
    FAIL = "FAIL", "不合格"
    PENDING = "PENDING", "待判定"
    NA = "NA", "不適用"


class InspectionRecord(models.Model):
    batch = models.ForeignKey(InspectionBatch, on_delete=models.PROTECT, related_name="records")
    inspector = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="inspection_records")
    inspection_date = models.DateTimeField(auto_now_add=True)
    overall_result = models.CharField(max_length=8, choices=ResultStatus.choices, default=ResultStatus.PENDING)
    remark = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = "inspection_records"


class InspectionResult(models.Model):
    inspection = models.ForeignKey(InspectionRecord, on_delete=models.CASCADE, related_name="results")
    product_item = models.ForeignKey(ProductInspectionItem, on_delete=models.PROTECT, related_name="results")
    measured_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    result = models.CharField(max_length=8, choices=ResultStatus.choices)
    standard_min_snapshot = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    standard_max_snapshot = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    inspection_method_snapshot = models.CharField(max_length=100, blank=True)
    unit_snapshot = models.CharField(max_length=30, blank=True)
    remark = models.TextField(blank=True)
    class Meta:
        db_table = "inspection_results"
        constraints = [models.UniqueConstraint(fields=["inspection", "product_item"], name="uq_inspection_product_item")]
