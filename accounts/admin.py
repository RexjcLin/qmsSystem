from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import Role, User


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "display_name", "description", "created_at")
    search_fields = ("name", "display_name", "description")

    def get_readonly_fields(self, request, obj=None):
        return ("name",) if obj else ()

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(User)
class QmsUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + ((_("QMS profile"), {"fields": ("full_name", "role", "status")}),)
    add_fieldsets = UserAdmin.add_fieldsets + ((_("QMS profile"), {"fields": ("full_name", "role", "status")}),)
    list_display = ("username", "full_name", "email", "role", "status", "is_staff", "is_active")
    list_filter = ("role", "status", "is_staff", "is_superuser", "is_active")
    search_fields = ("username", "full_name", "email")

    def get_readonly_fields(self, request, obj=None):
        fields = ("groups", "is_staff")
        if not request.user.is_superuser:
            fields += ("is_superuser", "user_permissions")
        return fields

    def has_change_permission(self, request, obj=None):
        if obj and obj.is_superuser and not request.user.is_superuser:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_superuser and not request.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)
