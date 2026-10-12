from importlib import import_module
from types import SimpleNamespace

from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import connection
from django.test import RequestFactory
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import Role, User
from .rbac import configure_role_groups


class RolePermissionTests(TestCase):
    def setUp(self):
        configure_role_groups()
        self.admin_role = Role.objects.create(name="ADMIN")
        self.manager_role = Role.objects.create(name="QUALITY_MANAGER")
        self.inspector_role = Role.objects.create(name="INSPECTOR")

    def test_role_changes_sync_group_staff_and_permissions(self):
        user = User.objects.create_user(username="manager", role=self.manager_role)
        self.assertTrue(user.is_staff)
        self.assertEqual(list(user.groups.values_list("name", flat=True)), ["QUALITY_MANAGER"])
        self.assertTrue(user.has_perm("products.change_product"))
        self.assertFalse(user.has_perm("products.delete_product"))
        self.assertFalse(user.has_perm("accounts.change_user"))

        user.role = self.inspector_role
        user.save()
        self.assertFalse(user.is_staff)
        self.assertEqual(list(user.groups.values_list("name", flat=True)), ["INSPECTOR"])
        self.assertTrue(user.has_perm("inspections.add_inspectionrecord"))
        self.assertFalse(user.has_perm("products.change_product"))

        user.role = None
        user.save()
        self.assertFalse(user.groups.filter(name__in=["ADMIN", "QUALITY_MANAGER", "INSPECTOR"]).exists())
        self.assertFalse(user.has_perm("inspections.view_inspectionrecord"))

    def test_direct_and_extra_group_permissions_cannot_exceed_role(self):
        user = User.objects.create_user(username="inspector", role=self.inspector_role)
        permission = Permission.objects.get(content_type__app_label="accounts", codename="change_user")
        user.user_permissions.add(permission)
        extra_group = Group.objects.create(name="Extra permissions")
        extra_group.permissions.add(permission)
        user.groups.add(extra_group)
        user.groups.add(Group.objects.get(name="ADMIN"))
        self.assertEqual(set(user.groups.values_list("name", flat=True)), {"INSPECTOR", "Extra permissions"})
        self.assertFalse(user.has_perm("accounts.change_user"))
        self.assertFalse(user.has_module_perms("accounts"))

    def test_superuser_without_role_can_access_api(self):
        user = User.objects.create_superuser(username="root", password="test-password", email="")
        client = APIClient()
        client.force_authenticate(user)
        self.assertEqual(client.get("/api/inspection/pending/").status_code, 200)
        self.assertTrue(user.has_perm("accounts.change_user"))

    def test_both_inactive_flags_block_authentication_and_api(self):
        for flag, value in (("status", "INACTIVE"), ("is_active", False)):
            with self.subTest(flag=flag):
                user = User.objects.create_user(username=flag, password="test-password", role=self.inspector_role)
                setattr(user, flag, value)
                user.save()
                self.assertFalse(self.client.login(username=flag, password="test-password"))
                client = APIClient()
                client.force_authenticate(user)
                self.assertEqual(client.get("/api/inspection/pending/").status_code, 403)
                self.assertFalse(user.has_perm("inspections.view_inspectionrecord"))

    def test_dashboard_requires_quality_view_permissions(self):
        user = User.objects.create_user(username="viewer")
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 403)
        user.role = self.inspector_role
        user.save()
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 200)

    def test_managed_group_cannot_be_removed_in_either_direction(self):
        user = User.objects.create_user(username="member", role=self.inspector_role)
        group = Group.objects.get(name="INSPECTOR")
        user.groups.clear()
        self.assertTrue(user.groups.filter(pk=group.pk).exists())
        group.user_set.clear()
        self.assertTrue(user.groups.filter(pk=group.pk).exists())

    def test_admin_cannot_edit_superuser_or_escalate_permissions(self):
        user = User.objects.create_user(username="admin", role=self.admin_role)
        root = User.objects.create_superuser(username="root", password="test-password", email="")
        request = RequestFactory().get("/admin/")
        request.user = user
        user_admin = admin.site._registry[User]
        self.assertTrue(user.has_perm("accounts.change_user"))
        self.assertFalse(user.has_perm("auth.change_group"))
        self.assertFalse(user_admin.has_change_permission(request, root))
        self.assertFalse(user_admin.has_delete_permission(request, root))
        self.assertTrue({"is_superuser", "groups", "user_permissions", "is_staff"}.issubset(
            user_admin.get_readonly_fields(request, user)
        ))

    def test_role_code_is_fixed_but_display_name_is_editable(self):
        self.inspector_role.display_name = "現場品管員"
        self.inspector_role.save()
        self.assertEqual(str(self.inspector_role), "現場品管員")
        self.inspector_role.name = "ADMIN"
        with self.assertRaises(ValidationError):
            self.inspector_role.save()
        with self.assertRaises(ValidationError):
            Role.objects.create(name="Unknown role")

    def test_sync_command_is_repeatable_and_preserves_passwords(self):
        user = User.objects.create_user(username="existing", password="test-password", role=self.manager_role)
        original_password = user.password
        call_command("sync_role_permissions")
        call_command("sync_role_permissions")
        user.refresh_from_db()
        self.assertEqual(user.password, original_password)
        self.assertEqual(user.groups.filter(name="QUALITY_MANAGER").count(), 1)
        self.assertEqual(Role.objects.count(), 3)
        self.assertEqual(Group.objects.filter(name__in=["ADMIN", "QUALITY_MANAGER", "INSPECTOR"]).count(), 3)

    def test_api_honors_group_permission_revocation(self):
        user = User.objects.create_user(username="revoked", role=self.inspector_role)
        group = Group.objects.get(name="INSPECTOR")
        permission = Permission.objects.get(content_type__app_label="inspections", codename="add_inspectionrecord")
        group.permissions.remove(permission)
        client = APIClient()
        client.force_authenticate(user)
        self.assertEqual(client.get("/api/inspection/pending/").status_code, 200)
        self.assertEqual(client.post("/api/inspection/submit/", {}, format="json").status_code, 403)

    def test_legacy_chinese_role_migration_preserves_user_and_password(self):
        Role.objects.bulk_create([Role(name="現場品管員", description="Existing description")])
        legacy = Role.objects.get(name="現場品管員")
        user = User.objects.create_user(username="legacy", password="test-password", role=legacy)
        password = user.password
        migration = import_module("accounts.migrations.0003_role_display_name_alter_role_name")
        migration.normalize_roles(apps, SimpleNamespace(connection=connection))
        user.refresh_from_db()
        self.assertEqual(user.role_id, self.inspector_role.pk)
        self.assertEqual(user.password, password)
        self.assertFalse(Role.objects.filter(pk=legacy.pk).exists())
        self.inspector_role.refresh_from_db()
        self.assertEqual(self.inspector_role.display_name, "現場品管員")
        self.assertEqual(self.inspector_role.description, "Existing description")