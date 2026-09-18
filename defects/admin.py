from django.contrib import admin

from .models import DefectImage, DefectRecord, DefectType


@admin.register(DefectType)
class DefectTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "updated_at")
    list_filter = ("status",)
    search_fields = ("name",)


class DefectImageInline(admin.TabularInline):
    model = DefectImage
    extra = 0


@admin.register(DefectRecord)
class DefectRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "defect_type", "inspection", "reported_by", "status", "created_at")
    list_filter = ("status", "defect_type")
    search_fields = ("inspection__batch__code", "defect_type__name", "reported_by__username")
    inlines = [DefectImageInline]


@admin.register(DefectImage)
class DefectImageAdmin(admin.ModelAdmin):
    list_display = ("defect", "image", "uploaded_at")
