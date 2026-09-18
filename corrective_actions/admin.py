from django.contrib import admin

from .models import CorrectiveAction


@admin.register(CorrectiveAction)
class CorrectiveActionAdmin(admin.ModelAdmin):
    list_display = ("id", "defect", "assigned_to", "status", "due_date", "completed_at")
    list_filter = ("status",)
    search_fields = ("defect__defect_type__name", "assigned_to__username", "action_description")
