from rest_framework.permissions import BasePermission


class RolePermission(BasePermission):
    allowed_roles = ()

    def has_permission(self, request, view):
        user = request.user
        role_name = getattr(getattr(user, "role", None), "name", "")
        return bool(
            user and user.is_authenticated and user.is_active and user.status == "ACTIVE"
            and (user.is_superuser or role_name in self.allowed_roles)
            and user.has_perms(getattr(view, "required_permissions", ()))
        )


class IsAdmin(RolePermission):
    allowed_roles = ("ADMIN",)


class IsQualityManager(RolePermission):
    allowed_roles = ("QUALITY_MANAGER",)


class IsInspector(RolePermission):
    allowed_roles = ("INSPECTOR",)


class CanAccessInspectionAPI(RolePermission):
    allowed_roles = ("ADMIN", "QUALITY_MANAGER", "INSPECTOR")
