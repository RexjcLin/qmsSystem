from django.contrib.auth.backends import ModelBackend

from .rbac import allowed_permission


class RoleBackend(ModelBackend):
    def user_can_authenticate(self, user):
        return super().user_can_authenticate(user) and user.status == "ACTIVE"

    def get_all_permissions(self, user_obj, obj=None):
        if not user_obj.is_authenticated or not self.user_can_authenticate(user_obj):
            return set()
        permissions = super().get_all_permissions(user_obj, obj)
        if user_obj.is_superuser:
            return permissions
        role_name = user_obj.role.name if user_obj.role_id else None
        return {
            permission for permission in permissions
            if allowed_permission(role_name, *permission.split(".", 1))
        }

    def has_module_perms(self, user_obj, app_label):
        return any(permission.startswith(f"{app_label}.") for permission in self.get_all_permissions(user_obj))