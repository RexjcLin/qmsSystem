from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import Role, User


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "created_at")
    search_fields = ("name", "description")


@admin.register(User)
class QmsUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + ((_("QMS profile"), {"fields": ("full_name", "role", "status")}),)
    add_fieldsets = UserAdmin.add_fieldsets + ((_("QMS profile"), {"fields": ("full_name", "role", "status")}),)
    list_display = ("username", "full_name", "email", "role", "status", "is_staff", "is_active")
    list_filter = ("role", "status", "is_staff", "is_superuser", "is_active")
    search_fields = ("username", "full_name", "email")
