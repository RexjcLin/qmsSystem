from django.db import models
from django.utils.translation import gettext_lazy as _


class ProductCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Category name"))
    description = models.CharField(max_length=255, blank=True, verbose_name=_("Description"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    class Meta:
        db_table = "product_categories"
        verbose_name = _("Product category")
        verbose_name_plural = _("Product categories")
    def __str__(self): return self.name


class Product(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name=_("Product code"))
    name = models.CharField(max_length=100, verbose_name=_("Product name"))
    category = models.ForeignKey(ProductCategory, null=True, blank=True, on_delete=models.SET_NULL, related_name="products", verbose_name=_("Category"))
    specification = models.TextField(blank=True, verbose_name=_("Specification"))
    status = models.CharField(max_length=10, choices=[("ACTIVE", _("Active")), ("INACTIVE", _("Inactive"))], default="ACTIVE", verbose_name=_("Status"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))
    class Meta:
        db_table = "products"
        indexes = [models.Index(fields=["name"]), models.Index(fields=["status"])]
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
    def __str__(self): return f"{self.code} {self.name}"


class InspectionItem(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Item name"))
    inspection_method = models.CharField(max_length=100, blank=True, verbose_name=_("Inspection method"))
    unit = models.CharField(max_length=30, blank=True, verbose_name=_("Unit"))
    standard_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name=_("Standard minimum"))
    standard_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name=_("Standard maximum"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    class Meta:
        db_table = "inspection_items"
        verbose_name = _("Inspection item")
        verbose_name_plural = _("Inspection items")
    def __str__(self): return self.name


class ProductInspectionItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="inspection_item_links", verbose_name=_("Product"))
    item = models.ForeignKey(InspectionItem, on_delete=models.CASCADE, related_name="product_links", verbose_name=_("Inspection item"))
    is_required = models.BooleanField(default=True, verbose_name=_("Required"))
    sort_order = models.PositiveIntegerField(default=0, verbose_name=_("Sort order"))
    class Meta:
        db_table = "product_inspection_items"
        constraints = [models.UniqueConstraint(fields=["product", "item"], name="uq_product_item")]
        ordering = ["sort_order", "id"]
        verbose_name = _("Product inspection item")
        verbose_name_plural = _("Product inspection items")
