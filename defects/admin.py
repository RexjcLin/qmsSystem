from django.contrib import admin
from .models import CorrectiveAction, DefectImage, DefectRecord, DefectType


@admin.register(DefectType)
class DefectTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "status")
    list_filter = ("status",)
    search_fields = ("name", "description")


@admin.register(DefectRecord)
class DefectRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "inspection", "defect_type", "status", "reported_by", "created_at")
    list_filter = ("status", "defect_type")
    search_fields = ("inspection__batch__code", "defect_type__name", "description", "reported_by__username", "reported_by__full_name")


@admin.register(DefectImage)
class DefectImageAdmin(admin.ModelAdmin):
    list_display = ("id", "defect", "uploaded_at")
    search_fields = ("defect__inspection__batch__code",)


@admin.register(CorrectiveAction)
class CorrectiveActionAdmin(admin.ModelAdmin):
    list_display = ("id", "defect", "assigned_to", "status", "due_date", "completed_at", "created_at")
    list_filter = ("status", "due_date")
    search_fields = ("defect__inspection__batch__code", "action_description", "assigned_to__username", "assigned_to__full_name")
