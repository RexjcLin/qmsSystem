from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import Role
from defects.models import CorrectiveAction, DefectRecord, DefectType
from inspections.models import BatchStatus, InspectionBatch, InspectionRecord, InspectionResult, ResultStatus
from products.models import InspectionItem, Product, ProductCategory, ProductInspectionItem


class Command(BaseCommand):
    help = "Create demo QMS data without overwriting existing records."

    @transaction.atomic
    def handle(self, *args, **options):
        roles = {}
        for name in ("ADMIN", "QUALITY_MANAGER", "INSPECTOR"):
            roles[name], _ = Role.objects.get_or_create(name=name)

        user, user_created = get_user_model().objects.get_or_create(
            username="demo_inspector",
            defaults={"full_name": "Demo Inspector", "role": roles["INSPECTOR"]},
        )
        if user_created:
            user.set_unusable_password()
            user.save(update_fields=["password"])

        category, _ = ProductCategory.objects.get_or_create(
            name="DEMO - Mechanical parts",
            defaults={"description": "Sample products for local testing."},
        )
        dimension, _ = InspectionItem.objects.get_or_create(
            name="DEMO - Outer diameter",
            defaults={
                "inspection_method": "Caliper",
                "unit": "mm",
                "standard_min": Decimal("9.90"),
                "standard_max": Decimal("10.10"),
            },
        )
        appearance, _ = InspectionItem.objects.get_or_create(
            name="DEMO - Appearance",
            defaults={"inspection_method": "Visual inspection", "description": "No scratches or burrs."},
        )
        products = []
        for index, name in enumerate(("Steel shaft", "Aluminum sleeve", "Plastic spacer"), start=1):
            product, _ = Product.objects.get_or_create(
                code=f"DEMO-P{index:03d}",
                defaults={"name": name, "category": category, "specification": "Outer diameter: 10.00 +/- 0.10 mm"},
            )
            for sort_order, item in enumerate((dimension, appearance), start=1):
                ProductInspectionItem.objects.get_or_create(
                    product=product, item=item,
                    defaults={"is_required": True, "sort_order": sort_order},
                )
            products.append(product)

        defect_type, _ = DefectType.objects.get_or_create(
            name="DEMO - Dimension out of tolerance",
            defaults={"description": "Measured diameter exceeds specification."},
        )
        scenarios = (
            (0, BatchStatus.PENDING, None, None),
            (1, BatchStatus.PENDING, None, None),
            (2, BatchStatus.PENDING, None, None),
            (0, BatchStatus.INSPECTING, None, None),
            (1, BatchStatus.COMPLETED, ResultStatus.PASS, None),
            (0, BatchStatus.COMPLETED, ResultStatus.FAIL, DefectRecord.Status.NEW),
            (1, BatchStatus.COMPLETED, ResultStatus.FAIL, DefectRecord.Status.PROCESSING),
            (2, BatchStatus.COMPLETED, ResultStatus.FAIL, DefectRecord.Status.CLOSED),
        )
        created_batches = 0
        for index, (product_index, status, outcome, defect_status) in enumerate(scenarios, start=1):
            batch, batch_created = InspectionBatch.objects.get_or_create(
                code=f"DEMO-B{index:03d}",
                defaults={"product": products[product_index], "quantity": 100, "status": status, "created_by": user},
            )
            if not batch_created:
                continue
            created_batches += 1
            if outcome is None:
                continue
            record = InspectionRecord.objects.create(
                batch=batch, inspector=user, overall_result=outcome, remark="Demo inspection.",
            )
            for link in batch.product.inspection_item_links.select_related("item"):
                item = link.item
                is_dimension = item.pk == dimension.pk
                failed = is_dimension and outcome == ResultStatus.FAIL
                InspectionResult.objects.create(
                    inspection=record,
                    product_item=link,
                    measured_value=Decimal("10.30" if failed else "10.00") if is_dimension else None,
                    result=ResultStatus.FAIL if failed else ResultStatus.PASS,
                    standard_min_snapshot=item.standard_min,
                    standard_max_snapshot=item.standard_max,
                    inspection_method_snapshot=item.inspection_method,
                    unit_snapshot=item.unit,
                )
            if defect_status is None:
                continue
            defect = DefectRecord.objects.create(
                inspection=record, defect_type=defect_type, reported_by=user,
                description="Outer diameter measured 10.30 mm; maximum allowed is 10.10 mm.",
                status=defect_status,
            )
            if defect_status in (DefectRecord.Status.PROCESSING, DefectRecord.Status.CLOSED):
                completed = defect_status == DefectRecord.Status.CLOSED
                CorrectiveAction.objects.create(
                    defect=defect, assigned_to=user,
                    action_description="Adjust tooling and reinspect the affected parts.",
                    due_date=timezone.localdate() + timedelta(days=7),
                    status=CorrectiveAction.Status.COMPLETED if completed else CorrectiveAction.Status.PROCESSING,
                    completed_at=timezone.now() if completed else None,
                )

        self.stdout.write(self.style.SUCCESS(f"Demo data ready. Created {created_batches} batches; existing records unchanged."))
        if user_created:
            self.stdout.write("demo_inspector has no usable password. Set one with: python manage.py changepassword demo_inspector")