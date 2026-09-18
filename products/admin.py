from django.contrib import admin

from .models import InspectionItem, InspectionItemOption, Product, ProductCategory, ProductInspectionItem


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "updated_at")
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "category", "status", "updated_at")
    list_filter = ("status", "category")
    search_fields = ("code", "name")


class InspectionItemOptionInline(admin.TabularInline):
    model = InspectionItemOption
    extra = 0


@admin.register(InspectionItem)
class InspectionItemAdmin(admin.ModelAdmin):
    list_display = ("name", "item_type", "inspection_method", "unit", "updated_at")
    list_filter = ("item_type",)
    search_fields = ("name",)
    inlines = [InspectionItemOptionInline]


@admin.register(ProductInspectionItem)
class ProductInspectionItemAdmin(admin.ModelAdmin):
    list_display = ("product", "item", "inspection_type", "is_required", "sort_order", "updated_at")
    list_filter = ("inspection_type", "is_required", "product")
    search_fields = ("product__code", "product__name", "item__name")
