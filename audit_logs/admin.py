from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "table_name", "record_id", "user", "created_at")
    list_filter = ("action", "table_name")
    search_fields = ("record_id", "table_name", "user__username")
    readonly_fields = ("created_at",)
