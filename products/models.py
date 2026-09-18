from django.db import models


class ProductStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "啟用"
    INACTIVE = "INACTIVE", "停用"


class InspectionItemType(models.TextChoices):
    NUMERIC = "NUMERIC", "數值"
    TEXT = "TEXT", "文字"
    BOOLEAN = "BOOLEAN", "布林"
    PASS_FAIL = "PASS_FAIL", "合格/不合格"
    OPTION = "OPTION", "選項"


class ProductCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "product_categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    category = models.ForeignKey(
        ProductCategory,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="products",
    )
    specification = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=ProductStatus.choices, default=ProductStatus.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products"
        indexes = [
            models.Index(fields=["category", "status"]),
            models.Index(fields=["name"]),
        ]
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} {self.name}"


class InspectionItem(models.Model):
    name = models.CharField(max_length=100)
    item_type = models.CharField(max_length=16, choices=InspectionItemType.choices, default=InspectionItemType.PASS_FAIL)
    inspection_method = models.CharField(max_length=100, blank=True)
    unit = models.CharField(max_length=30, blank=True)
    standard_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    standard_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    standard_value = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inspection_items"
        indexes = [models.Index(fields=["item_type"]), models.Index(fields=["name"])]
        ordering = ["name"]

    def __str__(self):
        return self.name


class InspectionItemOption(models.Model):
    item = models.ForeignKey(InspectionItem, on_delete=models.CASCADE, related_name="options")
    value = models.CharField(max_length=100)
    label = models.CharField(max_length=100)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inspection_item_options"
        constraints = [models.UniqueConstraint(fields=["item", "value"], name="uq_inspection_item_option")]
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.label


class ProductInspectionItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="inspection_item_links")
    item = models.ForeignKey(InspectionItem, on_delete=models.PROTECT, related_name="product_links")
    inspection_type = models.CharField(max_length=16, choices=InspectionItemType.choices)
    inspection_method = models.CharField(max_length=100, blank=True)
    standard_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    standard_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    standard_value = models.CharField(max_length=255, blank=True)
    is_required = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "product_inspection_items"
        constraints = [models.UniqueConstraint(fields=["product", "item"], name="uq_product_item")]
        indexes = [models.Index(fields=["product", "sort_order"])]
        ordering = ["sort_order", "id"]

    def save(self, *args, **kwargs):
        if not self.inspection_type:
            self.inspection_type = self.item.item_type
        if not self.inspection_method:
            self.inspection_method = self.item.inspection_method
        if self.standard_min is None:
            self.standard_min = self.item.standard_min
        if self.standard_max is None:
            self.standard_max = self.item.standard_max
        if not self.standard_value:
            self.standard_value = self.item.standard_value
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.code} - {self.item.name}"
