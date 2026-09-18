from django.contrib import admin

from .models import InspectionBatch, InspectionRecord, InspectionResult


@admin.register(InspectionBatch)
class InspectionBatchAdmin(admin.ModelAdmin):
    list_display = ("code", "product", "quantity", "status", "created_by", "created_at")
    list_filter = ("status", "product")
    search_fields = ("code", "product__code", "product__name")


@admin.register(InspectionRecord)
class InspectionRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "batch", "inspector", "overall_result", "inspection_date")
    list_filter = ("overall_result",)
    search_fields = ("batch__code", "inspector__username", "inspector__full_name")


@admin.register(InspectionResult)
class InspectionResultAdmin(admin.ModelAdmin):
    list_display = ("inspection", "product_inspection_item", "result", "measured_value", "measured_text")
    list_filter = ("result", "inspection_type_snapshot")
    search_fields = ("inspection__batch__code", "product_inspection_item__item__name")
