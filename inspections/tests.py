from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Role
from inspections.models import InspectionBatch, InspectionRecord, InspectionResult
from products.models import InspectionItem, Product, ProductCategory, ProductInspectionItem


class SubmitInspectionAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.role = Role.objects.create(name="INSPECTOR")
        self.user = get_user_model().objects.create_user(username="inspector", role=self.role)
        self.client.force_authenticate(self.user)

        self.category = ProductCategory.objects.create(name="電子件")
        self.product = Product.objects.create(code="P-001", name="測試產品", category=self.category)
        item_1 = InspectionItem.objects.create(
            name="尺寸",
            inspection_method="游標卡尺",
            unit="mm",
            standard_min=Decimal("5.00"),
            standard_max=Decimal("5.20"),
        )
        item_2 = InspectionItem.objects.create(
            name="外觀",
            inspection_method="目視",
            unit="",
        )
        self.product_item_required = ProductInspectionItem.objects.create(product=self.product, item=item_1, is_required=True, sort_order=1)
        self.product_item_optional = ProductInspectionItem.objects.create(product=self.product, item=item_2, is_required=False, sort_order=2)
        self.batch = InspectionBatch.objects.create(code="BATCH-001", product=self.product, quantity=10, created_by=self.user)

    def test_submit_uses_product_item_and_persists_snapshots(self):
        response = self.client.post("/api/inspection/submit/", {
            "batch_id": self.batch.id,
            "remark": "首件檢驗",
            "results": [{
                "product_item_id": self.product_item_required.id,
                "measured_value": "5.10",
                "result": "PASS",
            }],
        }, format="json")

        self.assertEqual(response.status_code, 201)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.status, "COMPLETED")

        record = InspectionRecord.objects.get(batch=self.batch)
        result = InspectionResult.objects.get(inspection=record)
        self.assertEqual(record.overall_result, "PASS")
        self.assertEqual(result.product_item_id, self.product_item_required.id)
        self.assertEqual(result.standard_min_snapshot, Decimal("5.00"))
        self.assertEqual(result.standard_max_snapshot, Decimal("5.20"))
        self.assertEqual(result.inspection_method_snapshot, "游標卡尺")
        self.assertEqual(result.unit_snapshot, "mm")

    def test_submit_requires_all_required_items(self):
        required_item = InspectionItem.objects.create(name="重量")
        missing_product_item = ProductInspectionItem.objects.create(product=self.product, item=required_item, is_required=True, sort_order=3)

        response = self.client.post("/api/inspection/submit/", {
            "batch_id": self.batch.id,
            "results": [{
                "product_item_id": self.product_item_required.id,
                "result": "PASS",
            }],
        }, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("errors", response.data)
        self.assertIn("missing_required_product_item_ids", response.data["errors"])
        self.assertEqual(
            [int(item) for item in response.data["errors"]["missing_required_product_item_ids"]],
            [missing_product_item.id],
        )

    def test_submit_marks_overall_fail_when_required_item_fails(self):
        response = self.client.post("/api/inspection/submit/", {
            "batch_id": self.batch.id,
            "results": [{
                "product_item_id": self.product_item_required.id,
                "measured_value": "5.30",
                "result": "FAIL",
            }],
        }, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["overall_result"], "FAIL")

    def test_submit_marks_overall_fail_when_optional_item_fails(self):
        response = self.client.post("/api/inspection/submit/", {
            "batch_id": self.batch.id,
            "results": [
                {
                    "product_item_id": self.product_item_required.id,
                    "measured_value": "5.10",
                    "result": "PASS",
                },
                {
                    "product_item_id": self.product_item_optional.id,
                    "result": "FAIL",
                },
            ],
        }, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["overall_result"], "FAIL")

    def test_submit_rolls_back_when_result_save_fails(self):
        self.client.raise_request_exception = False
        with patch("inspections.serializers.InspectionResult.objects.bulk_create", side_effect=RuntimeError("boom")):
            response = self.client.post("/api/inspection/submit/", {
                "batch_id": self.batch.id,
                "results": [{
                    "product_item_id": self.product_item_required.id,
                    "result": "PASS",
                }],
            }, format="json")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data["errors"]["detail"], "檢驗結果提交失敗。")
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.status, "PENDING")
        self.assertFalse(InspectionRecord.objects.filter(batch=self.batch).exists())

    def test_inspection_api_requires_inspector_role(self):
        other_user = get_user_model().objects.create_user(username="viewer")
        self.client.force_authenticate(other_user)

        response = self.client.get("/api/inspection/pending/")

        self.assertEqual(response.status_code, 403)
        self.assertIn("errors", response.data)
