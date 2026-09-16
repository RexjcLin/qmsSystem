from django.db import models


class ProductCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = "product_categories"
    def __str__(self): return self.name


class Product(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    category = models.ForeignKey(ProductCategory, null=True, blank=True, on_delete=models.SET_NULL, related_name="products")
    specification = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=[("ACTIVE", "啟用"), ("INACTIVE", "停用")], default="ACTIVE")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = "products"
        indexes = [models.Index(fields=["name"]), models.Index(fields=["status"])]
    def __str__(self): return f"{self.code} {self.name}"


class InspectionItem(models.Model):
    name = models.CharField(max_length=100)
    inspection_method = models.CharField(max_length=100, blank=True)
    unit = models.CharField(max_length=30, blank=True)
    standard_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    standard_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = "inspection_items"
    def __str__(self): return self.name


class ProductInspectionItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="inspection_item_links")
    item = models.ForeignKey(InspectionItem, on_delete=models.CASCADE, related_name="product_links")
    is_required = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    class Meta:
        db_table = "product_inspection_items"
        constraints = [models.UniqueConstraint(fields=["product", "item"], name="uq_product_item")]
        ordering = ["sort_order", "id"]
