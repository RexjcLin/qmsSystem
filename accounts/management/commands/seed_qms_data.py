import os
from decimal import Decimal

from django.core.management.base import BaseCommand

from accounts.models import Role, RoleChoices, User
from defects.models import DefectType
from products.models import InspectionItem, InspectionItemType, Product, ProductCategory, ProductInspectionItem


class Command(BaseCommand):
    help = "Create idempotent QMS seed data."

    def handle(self, *args, **options):
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
                "password": os.getenv("QMS_ADMIN_PASSWORD", "ChangeMeAdmin123!"),
                "is_staff": True,
                "is_superuser": True,
            },
            {
                "username": "quality.manager",
                "full_name": "Quality Manager",
                "email": "manager@example.com",
                "role": role_objects[RoleChoices.QUALITY_MANAGER],
                "password": os.getenv("QMS_MANAGER_PASSWORD", "ChangeMeManager123!"),
                "is_staff": True,
                "is_superuser": False,
            },
            {
                "username": "inspector",
                "full_name": "Inspector",
                "email": "inspector@example.com",
                "role": role_objects[RoleChoices.INSPECTOR],
                "password": os.getenv("QMS_INSPECTOR_PASSWORD", "ChangeMeInspector123!"),
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
            if created or not user.check_password(spec["password"]):
                user.set_password(spec["password"])
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
