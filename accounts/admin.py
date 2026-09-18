from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Role, User


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "updated_at")
    search_fields = ("name", "description")


@admin.register(User)
class QMSUserAdmin(UserAdmin):
    list_display = ("username", "full_name", "email", "role", "status", "is_staff")
    list_filter = ("role", "status", "is_staff", "is_superuser")
    fieldsets = UserAdmin.fieldsets + (
        ("QMS", {"fields": ("full_name", "role", "status", "created_at", "updated_at")}),
    )
    readonly_fields = ("created_at", "updated_at")
