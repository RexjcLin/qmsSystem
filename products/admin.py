from django.contrib import admin
from .models import ProductCategory, Product, InspectionItem, ProductInspectionItem


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "created_at")
    search_fields = ("name", "description")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "category", "status", "created_at", "updated_at")
    list_filter = ("status", "category")
    search_fields = ("code", "name", "specification")


@admin.register(InspectionItem)
class InspectionItemAdmin(admin.ModelAdmin):
    list_display = ("name", "inspection_method", "unit", "standard_min", "standard_max", "created_at")
    search_fields = ("name", "inspection_method", "description")


@admin.register(ProductInspectionItem)
class ProductInspectionItemAdmin(admin.ModelAdmin):
    list_display = ("product", "item", "is_required", "sort_order")
    list_filter = ("product", "is_required")
    search_fields = ("product__name", "product__code", "item__name")
