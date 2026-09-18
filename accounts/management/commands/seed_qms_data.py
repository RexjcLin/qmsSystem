import os
import secrets
from decimal import Decimal

from django.core.management.base import BaseCommand

from accounts.models import Role, RoleChoices, User
from defects.models import DefectType
from products.models import InspectionItem, InspectionItemType, Product, ProductCategory, ProductInspectionItem


class Command(BaseCommand):
    help = "Create idempotent QMS seed data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset-passwords",
            action="store_true",
            help="Reset representative user passwords on existing seed accounts.",
        )

    def handle(self, *args, **options):
        reset_passwords = options["reset_passwords"]
        roles = {
            RoleChoices.ADMIN: "系統管理員",
            RoleChoices.QUALITY_MANAGER: "品質主管",
            RoleChoices.INSPECTOR: "檢驗人員",
        }
        role_objects = {}
        for name, description in roles.items():
            role_objects[name], _ = Role.objects.update_or_create(name=name, defaults={"description": description})

        users = [
            {
                "username": "admin",
                "full_name": "QMS Admin",
                "email": "admin@example.com",
                "role": role_objects[RoleChoices.ADMIN],
                "password_env": "QMS_ADMIN_PASSWORD",
                "is_staff": True,
                "is_superuser": True,
            },
            {
                "username": "quality.manager",
                "full_name": "Quality Manager",
                "email": "manager@example.com",
                "role": role_objects[RoleChoices.QUALITY_MANAGER],
                "password_env": "QMS_MANAGER_PASSWORD",
                "is_staff": True,
                "is_superuser": False,
            },
            {
                "username": "inspector",
                "full_name": "Inspector",
                "email": "inspector@example.com",
                "role": role_objects[RoleChoices.INSPECTOR],
                "password_env": "QMS_INSPECTOR_PASSWORD",
                "is_staff": True,
                "is_superuser": False,
            },
        ]
        for spec in users:
            user, created = User.objects.get_or_create(
                username=spec["username"],
                defaults={
                    "full_name": spec["full_name"],
                    "email": spec["email"],
                    "role": spec["role"],
                    "status": "ACTIVE",
                    "is_staff": spec["is_staff"],
                    "is_superuser": spec["is_superuser"],
                },
            )
            changed = created
            for field in ("full_name", "email", "role", "is_staff", "is_superuser"):
                value = spec[field]
                if getattr(user, field) != value:
                    setattr(user, field, value)
                    changed = True
            if created or reset_passwords:
                password = os.getenv(spec["password_env"])
                if not password:
                    password = secrets.token_urlsafe(18)
                    self.stdout.write(
                        self.style.WARNING(
                            f"Generated one-time local password for {spec['username']}: {password}"
                        )
                    )
                user.set_password(password)
                changed = True
            if changed:
                user.save()

        category, _ = ProductCategory.objects.update_or_create(
            name="Electronic Components",
            defaults={"description": "MVP sample category"},
        )
        product, _ = Product.objects.update_or_create(
            code="QMS-DEMO-001",
            defaults={
                "name": "Demo Power Module",
                "category": category,
                "specification": "5V 輸出模組",
                "status": "ACTIVE",
            },
        )
        items = [
            {
                "name": "Voltage",
                "item_type": InspectionItemType.NUMERIC,
                "inspection_method": "Multimeter",
                "unit": "V",
                "standard_min": Decimal("4.90"),
                "standard_max": Decimal("5.10"),
                "standard_value": "5.00",
            },
            {
                "name": "Dimensions",
                "item_type": InspectionItemType.NUMERIC,
                "inspection_method": "Caliper",
                "unit": "mm",
                "standard_min": Decimal("9.80"),
                "standard_max": Decimal("10.20"),
                "standard_value": "10.00",
            },
            {
                "name": "Visual Inspection",
                "item_type": InspectionItemType.PASS_FAIL,
                "inspection_method": "Visual",
                "unit": "",
                "standard_min": None,
                "standard_max": None,
                "standard_value": "PASS",
            },
            {
                "name": "Functional Test",
                "item_type": InspectionItemType.BOOLEAN,
                "inspection_method": "Power-on functional verification",
                "unit": "",
                "standard_min": None,
                "standard_max": None,
                "standard_value": "TRUE",
            },
        ]
        sort_order = 10
        for item_spec in items:
            item, _ = InspectionItem.objects.update_or_create(
                name=item_spec["name"],
                defaults=item_spec | {"description": "Seed data"},
            )
            ProductInspectionItem.objects.update_or_create(
                product=product,
                item=item,
                defaults={
                    "inspection_type": item.item_type,
                    "inspection_method": item.inspection_method,
                    "standard_min": item.standard_min,
                    "standard_max": item.standard_max,
                    "standard_value": item.standard_value,
                    "is_required": True,
                    "sort_order": sort_order,
                },
            )
            sort_order += 10

        DefectType.objects.update_or_create(
            name="Scratch",
            defaults={"description": "Surface scratch", "status": "ACTIVE"},
        )
        self.stdout.write(self.style.SUCCESS("QMS seed data ensured successfully."))
