from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.test import TestCase

from accounts.models import Role, RoleChoices, User
from corrective_actions.models import CorrectiveAction, CorrectiveActionStatus
from defects.models import DefectRecord, DefectStatus, DefectType, DefectTypeStatus, DefectImage
from inspections.models import (
    BatchStatus,
    InspectionBatch,
    InspectionItemResult,
    InspectionOverallResult,
    InspectionRecord,
    InspectionResult,
)
from products.models import (
    InspectionItem,
    InspectionItemType,
    Product,
    ProductCategory,
    ProductInspectionItem,
    ProductStatus,
)


class QMSModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        role = Role.objects.create(name=RoleChoices.INSPECTOR, description="Inspector")
        cls.user = User.objects.create_user(
            "inspector",
            "",
            "test-pass-123",
            role=role,
            full_name="Inspector",
        )
        cls.category = ProductCategory.objects.create(name="Category A")
        cls.product = Product.objects.create(code="P-001", name="Product A", category=cls.category)
        cls.item = InspectionItem.objects.create(
            name="Voltage",
            item_type=InspectionItemType.NUMERIC,
            inspection_method="Multimeter",
            unit="V",
            standard_min="4.90",
            standard_max="5.10",
            standard_value="5.00",
        )
        cls.product_item = ProductInspectionItem.objects.create(
            product=cls.product,
            item=cls.item,
            inspection_type=InspectionItemType.NUMERIC,
            inspection_method="Multimeter",
            standard_min="4.90",
            standard_max="5.10",
            standard_value="5.00",
            is_required=True,
            sort_order=1,
        )
        cls.batch = InspectionBatch.objects.create(code="BATCH-001", product=cls.product, quantity=10, created_by=cls.user)

    def test_product_inspection_item_unique_per_product_and_item(self):
        with self.assertRaises(IntegrityError):
            ProductInspectionItem.objects.create(
                product=self.product,
                item=self.item,
                inspection_type=InspectionItemType.NUMERIC,
            )

    def test_inspection_result_keeps_configuration_snapshot(self):
        record = InspectionRecord.objects.create(batch=self.batch, inspector=self.user)
        result = InspectionResult.objects.create(
            inspection=record,
            product_inspection_item=self.product_item,
            measured_value="5.00",
            result=InspectionItemResult.PASS,
            inspection_type_snapshot="",
        )
        self.product_item.inspection_method = "Updated Method"
        self.product_item.standard_min = "4.80"
        self.product_item.standard_max = "5.20"
        self.product_item.standard_value = "5.10"
        self.product_item.save()
        result.refresh_from_db()
        self.assertEqual(result.inspection_method_snapshot, "Multimeter")
        self.assertEqual(str(result.standard_min_snapshot), "4.90")
        self.assertEqual(str(result.standard_max_snapshot), "5.10")
        self.assertEqual(result.standard_value_snapshot, "5.00")

    def test_key_status_defaults(self):
        record = InspectionRecord.objects.create(batch=self.batch, inspector=self.user)
        defect_type = DefectType.objects.create(name="Scratch", status=DefectTypeStatus.ACTIVE)
        defect = DefectRecord.objects.create(inspection=record, defect_type=defect_type, reported_by=self.user)
        action = CorrectiveAction.objects.create(defect=defect, action_description="Polish surface")

        self.assertEqual(self.product.status, ProductStatus.ACTIVE)
        self.assertEqual(self.batch.status, BatchStatus.PENDING)
        self.assertEqual(record.overall_result, InspectionOverallResult.PENDING)
        self.assertEqual(defect.status, DefectStatus.NEW)
        self.assertEqual(action.status, CorrectiveActionStatus.PENDING)

    def test_cascade_and_protect_relationships(self):
        record = InspectionRecord.objects.create(batch=self.batch, inspector=self.user)
        result = InspectionResult.objects.create(
            inspection=record,
            product_inspection_item=self.product_item,
            measured_value="5.00",
            result=InspectionItemResult.PASS,
            inspection_type_snapshot="",
        )
        result_id = result.id
        record.delete()
        self.assertFalse(InspectionResult.objects.filter(id=result_id).exists())

        record = InspectionRecord.objects.create(batch=self.batch, inspector=self.user)
        defect_type = DefectType.objects.create(name="Dent", status=DefectTypeStatus.ACTIVE)
        defect = DefectRecord.objects.create(inspection=record, defect_type=defect_type, reported_by=self.user)
        DefectImage.objects.create(
            defect=defect,
            image=SimpleUploadedFile("defect.jpg", b"filecontent", content_type="image/jpeg"),
        )
        CorrectiveAction.objects.create(defect=defect, action_description="Replace housing")
        with self.assertRaises(ProtectedError):
            defect.delete()
