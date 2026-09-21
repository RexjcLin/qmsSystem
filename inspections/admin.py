from django.contrib import admin
from .models import InspectionBatch, InspectionRecord, InspectionResult


@admin.register(InspectionBatch)
class InspectionBatchAdmin(admin.ModelAdmin):
    list_display = ("code", "product", "quantity", "status", "created_by", "created_at")
    list_filter = ("status", "product")
    search_fields = ("code", "product__name", "product__code")


@admin.register(InspectionRecord)
class InspectionRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "batch", "inspector", "overall_result", "inspection_date", "created_at")
    list_filter = ("overall_result",)
    search_fields = ("batch__code", "inspector__username", "inspector__full_name", "remark")


@admin.register(InspectionResult)
class InspectionResultAdmin(admin.ModelAdmin):
    list_display = ("inspection", "item", "measured_value", "result")
    list_filter = ("result",)
    search_fields = ("inspection__batch__code", "item__name", "remark")
