from contextvars import ContextVar

from django.contrib.auth.models import Group, Permission


ROLE_LABELS = {
    "ADMIN": "管理員",
    "QUALITY_MANAGER": "品質主管",
    "INSPECTOR": "現場品管員",
}
BUSINESS_APPS = {"products", "inspections", "defects"}
SYNCING_ROLE = ContextVar("syncing_role", default=False)


def allowed_permission(role_name, app_label, codename):
    if role_name == "ADMIN":
        return app_label in BUSINESS_APPS or (
            app_label == "accounts"
            and (codename.endswith("_user") or codename in {"view_role", "change_role"})
        )
    if role_name == "QUALITY_MANAGER":
        return app_label in BUSINESS_APPS and not codename.startswith("delete_")
    if role_name == "INSPECTOR":
        return app_label in BUSINESS_APPS and (
            codename.startswith("view_")
            or codename in {"add_inspectionrecord", "add_inspectionresult", "change_inspectionbatch"}
        )
    return False


def configure_role_groups(using="default"):
    permissions = list(Permission.objects.using(using).select_related("content_type"))
    for role_name in ROLE_LABELS:
        group, _ = Group.objects.using(using).get_or_create(name=role_name)
        group.permissions.set([
            permission for permission in permissions
            if allowed_permission(role_name, permission.content_type.app_label, permission.codename)
        ])


def sync_user_role(user, using="default"):
    if SYNCING_ROLE.get():
        return
    token = SYNCING_ROLE.set(True)
    try:
        _sync_user_role(user, using)
    finally:
        SYNCING_ROLE.reset(token)


def _sync_user_role(user, using):
    role_name = user.role.name if user.role_id else None
    managed_groups = Group.objects.using(using).filter(name__in=ROLE_LABELS)
    obsolete_groups = managed_groups.exclude(name=role_name)
    user.groups.remove(*obsolete_groups)
    if role_name in ROLE_LABELS:
        group, _ = Group.objects.using(using).get_or_create(name=role_name)
        if not user.groups.filter(pk=group.pk).exists():
            user.groups.add(group)
    is_staff = user.is_superuser or role_name in {"ADMIN", "QUALITY_MANAGER"}
    if user.is_staff != is_staff:
        type(user).objects.using(using).filter(pk=user.pk).update(is_staff=is_staff)
        user.is_staff = is_staff
    for cache_name in ("_perm_cache", "_group_perm_cache", "_user_perm_cache"):
        user.__dict__.pop(cache_name, None)