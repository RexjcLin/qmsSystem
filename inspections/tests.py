from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.exceptions import ValidationError

from accounts.models import Role
from defects.models import CorrectiveAction, DefectRecord
from inspections.models import InspectionBatch, InspectionRecord, InspectionResult
from inspections.serializers import SubmitInspectionSerializer
from products.models import InspectionItem, Product, ProductCategory, ProductInspectionItem


class SeedDemoDataTests(TestCase):
    def test_creates_complete_scenarios_and_snapshots(self):
        call_command("seed_demo_data", verbosity=0)

        self.assertEqual(Product.objects.count(), 3)
        self.assertEqual(ProductInspectionItem.objects.count(), 6)
        self.assertEqual(InspectionBatch.objects.count(), 8)
        self.assertEqual(InspectionBatch.objects.filter(status="PENDING").count(), 3)
        self.assertEqual(InspectionRecord.objects.count(), 4)
        self.assertEqual(InspectionResult.objects.count(), 8)
        self.assertEqual(DefectRecord.objects.count(), 3)
        self.assertEqual(CorrectiveAction.objects.count(), 2)
        self.assertFalse(get_user_model().objects.get(username="demo_inspector").has_usable_password())
        for result in InspectionResult.objects.select_related("product_item__item"):
            item = result.product_item.item
            self.assertEqual(result.standard_min_snapshot, item.standard_min)
            self.assertEqual(result.standard_max_snapshot, item.standard_max)
            self.assertEqual(result.inspection_method_snapshot, item.inspection_method)
            self.assertEqual(result.unit_snapshot, item.unit)

    def test_rerun_preserves_existing_data_and_credentials(self):
        user = get_user_model().objects.create_user(username="demo_inspector", password="existing-test-password")
        call_command("seed_demo_data", verbosity=0)
        batch = InspectionBatch.objects.get(code="DEMO-B001")
        batch.status = "CANCELLED"
        batch.save()
        product = Product.objects.get(code="DEMO-P001")
        product.name = "User edited product"
        product.save()

        call_command("seed_demo_data", verbosity=0)

        self.assertEqual(InspectionBatch.objects.count(), 8)
        self.assertEqual(InspectionRecord.objects.count(), 4)
        self.assertEqual(InspectionResult.objects.count(), 8)
        self.assertEqual(DefectRecord.objects.count(), 3)
        self.assertEqual(CorrectiveAction.objects.count(), 2)
        batch.refresh_from_db()
        product.refresh_from_db()
        user.refresh_from_db()
        self.assertEqual(batch.status, "CANCELLED")
        self.assertEqual(product.name, "User edited product")
        self.assertTrue(user.check_password("existing-test-password"))
        self.assertIsNone(user.role)


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

    def test_submit_rejects_na_for_required_item(self):
        response = self.client.post("/api/inspection/submit/", {
            "batch_id": self.batch.id,
            "results": [{
                "product_item_id": self.product_item_required.id,
                "result": "NA",
            }],
        }, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["errors"]["results"][0], "必填檢驗項目不可標記為 NA。")
        self.assertEqual(
            [int(item) for item in response.data["errors"]["required_na_product_item_ids"]],
            [self.product_item_required.id],
        )

    def test_submit_rejects_legacy_item_id_payload(self):
        response = self.client.post("/api/inspection/submit/", {
            "batch_id": self.batch.id,
            "results": [{
                "item_id": self.product_item_required.item_id,
                "result": "PASS",
            }],
        }, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["errors"]["results"][0]["product_item_id"][0], "此為必需欄位。")

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
        defect = DefectRecord.objects.get(inspection_id=response.data["inspection_id"])
        self.assertEqual(response.data["defect_ids"], [defect.pk])
        self.assertEqual(defect.reported_by, self.user)
        self.assertIn("5.30", defect.description)

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

    def test_submit_accepts_unclaimed_inspecting_batch(self):
        self.batch.status = "INSPECTING"
        self.batch.save(update_fields=["status", "updated_at"])

        response = self.client.post("/api/inspection/submit/", {
            "batch_id": self.batch.id,
            "results": [{
                "product_item_id": self.product_item_required.id,
                "measured_value": "5.10",
                "result": "PASS",
            }],
        }, format="json")

        self.assertEqual(response.status_code, 201)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.assigned_inspector, self.user)

    def test_start_resume_release_and_submit_batch(self):
        start_url = f"/api/inspection/batches/{self.batch.pk}/start/"
        for attempt in range(2):
            self.assertEqual(self.client.post(start_url).status_code, 200)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.status, "INSPECTING")
        self.assertEqual(self.batch.assigned_inspector, self.user)
        self.assertEqual(self.client.post(f"/api/inspection/batches/{self.batch.pk}/release/").status_code, 200)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.status, "PENDING")
        self.assertIsNone(self.batch.assigned_inspector)
        self.assertEqual(self.client.post(start_url).status_code, 200)
        payload = {"batch_id": self.batch.pk, "results": [{
            "product_item_id": self.product_item_required.pk, "measured_value": "5.10", "result": "PASS",
        }]}
        self.assertEqual(self.client.post("/api/inspection/submit/", payload, format="json").status_code, 201)
        self.assertEqual(self.client.post("/api/inspection/submit/", payload, format="json").status_code, 400)
        self.assertEqual(self.client.post(start_url).status_code, 400)
        self.assertEqual(self.client.post(f"/api/inspection/batches/{self.batch.pk}/release/").status_code, 400)
        self.assertEqual(InspectionRecord.objects.filter(batch=self.batch).count(), 1)

    def test_other_inspector_cannot_claim_release_or_submit_owned_batch(self):
        self.client.post(f"/api/inspection/batches/{self.batch.pk}/start/")
        other = get_user_model().objects.create_user(username="other", role=self.role)
        self.client.force_authenticate(other)
        self.assertEqual(self.client.post(f"/api/inspection/batches/{self.batch.pk}/start/").status_code, 403)
        self.assertEqual(self.client.post(f"/api/inspection/batches/{self.batch.pk}/release/").status_code, 403)
        response = self.client.post("/api/inspection/submit/", {
            "batch_id": self.batch.pk,
            "results": [{"product_item_id": self.product_item_required.pk, "measured_value": "5.10", "result": "PASS"}],
        }, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.get("/api/inspection/pending/").data, [])
        manager_role = Role.objects.create(name="QUALITY_MANAGER")
        manager = get_user_model().objects.create_user(username="supervisor", role=manager_role)
        self.client.force_authenticate(manager)
        self.assertEqual(self.client.post(f"/api/inspection/batches/{self.batch.pk}/release/").status_code, 200)

    def test_cancelled_batch_cannot_be_started_or_submitted(self):
        self.batch.status = "CANCELLED"
        self.batch.save()
        self.assertEqual(self.client.post(f"/api/inspection/batches/{self.batch.pk}/start/").status_code, 400)
        response = self.client.post("/api/inspection/submit/", {
            "batch_id": self.batch.pk,
            "results": [{"product_item_id": self.product_item_required.pk, "measured_value": "5.10", "result": "PASS"}],
        }, format="json")
        self.assertEqual(response.status_code, 400)

    def test_submit_rolls_back_when_result_save_fails(self):
        self.client.raise_request_exception = False
        with patch("inspections.serializers.InspectionResult.objects.bulk_create", side_effect=RuntimeError("boom")):
            response = self.client.post("/api/inspection/submit/", {
                "batch_id": self.batch.id,
                "results": [{
                    "product_item_id": self.product_item_required.id,
                    "measured_value": "5.10",
                    "result": "PASS",
                }],
            }, format="json")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data["errors"]["detail"], "檢驗結果提交失敗。")
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.status, "PENDING")
        self.assertFalse(InspectionRecord.objects.filter(batch=self.batch).exists())

    def test_submit_rejects_missing_or_out_of_range_pass_measurements(self):
        for value in (None, "4.99", "5.21"):
            with self.subTest(value=value):
                response = self.client.post("/api/inspection/submit/", {
                    "batch_id": self.batch.pk,
                    "results": [{"product_item_id": self.product_item_required.pk, "measured_value": value, "result": "PASS"}],
                }, format="json")
                self.assertEqual(response.status_code, 400)
                self.assertFalse(InspectionRecord.objects.filter(batch=self.batch).exists())

    def test_submit_accepts_measurement_at_standard_boundary(self):
        response = self.client.post("/api/inspection/submit/", {
            "batch_id": self.batch.pk,
            "results": [{"product_item_id": self.product_item_required.pk, "measured_value": "5.20", "result": "PASS"}],
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["defect_ids"], [])

    def test_submit_rejects_no_items_empty_results_and_all_na(self):
        for link in self.product.inspection_item_links.all():
            link.is_required = False
            link.save()
        for results in ([], [{"product_item_id": self.product_item_optional.pk, "result": "NA"}]):
            response = self.client.post("/api/inspection/submit/", {"batch_id": self.batch.pk, "results": results}, format="json")
            self.assertEqual(response.status_code, 400)
        self.product.inspection_item_links.all().delete()
        self.assertEqual(self.client.post(f"/api/inspection/batches/{self.batch.pk}/start/").status_code, 400)
        response = self.client.post("/api/inspection/submit/", {"batch_id": self.batch.pk, "results": []}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_submit_checks_single_sided_limits(self):
        item = self.product_item_required.item
        for minimum, maximum, value in ((None, Decimal("5.20"), "5.21"), (Decimal("5.00"), None, "4.99")):
            item.standard_min = minimum
            item.standard_max = maximum
            item.save()
            response = self.client.post("/api/inspection/submit/", {
                "batch_id": self.batch.pk,
                "results": [{"product_item_id": self.product_item_required.pk, "measured_value": value, "result": "PASS"}],
            }, format="json")
            self.assertEqual(response.status_code, 400)

    def test_submit_revalidates_standard_changes_before_saving(self):
        serializer = SubmitInspectionSerializer(data={
            "batch_id": self.batch.pk,
            "results": [{"product_item_id": self.product_item_required.pk, "measured_value": "5.10", "result": "PASS"}],
        }, context={"request": SimpleNamespace(user=self.user)})
        self.assertTrue(serializer.is_valid())
        item = self.product_item_required.item
        item.standard_max = Decimal("5.00")
        item.save()
        with self.assertRaises(ValidationError):
            serializer.save()
        self.assertFalse(InspectionRecord.objects.exists())

    def test_defect_creation_failure_rolls_back_inspection_and_results(self):
        with patch("inspections.serializers.DefectRecord.objects.create", side_effect=RuntimeError("boom")):
            response = self.client.post("/api/inspection/submit/", {
                "batch_id": self.batch.pk,
                "results": [{"product_item_id": self.product_item_required.pk, "measured_value": "5.30", "result": "FAIL"}],
            }, format="json")
        self.assertEqual(response.status_code, 500)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.status, "PENDING")
        self.assertFalse(InspectionRecord.objects.filter(batch=self.batch).exists())
        self.assertFalse(InspectionResult.objects.exists())
        self.assertFalse(DefectRecord.objects.exists())

    def test_inspection_api_requires_inspector_role(self):
        other_user = get_user_model().objects.create_user(username="viewer")
        self.client.force_authenticate(other_user)

        response = self.client.get("/api/inspection/pending/")

        self.assertEqual(response.status_code, 403)
        self.assertIn("errors", response.data)

    def test_quality_manager_can_access_pending_batches(self):
        manager_role = Role.objects.create(name="QUALITY_MANAGER")
        manager = get_user_model().objects.create_user(username="manager", role=manager_role)
        self.client.force_authenticate(manager)

        response = self.client.get("/api/inspection/pending/")

        self.assertEqual(response.status_code, 200)

    def test_product_items_endpoint_requires_role(self):
        other_user = get_user_model().objects.create_user(username="viewer-products")
        self.client.force_authenticate(other_user)

        response = self.client.get(f"/api/products/{self.product.id}/inspection-items/")

        self.assertEqual(response.status_code, 403)
        self.assertIn("errors", response.data)

    def test_submit_endpoint_requires_role(self):
        other_user = get_user_model().objects.create_user(username="viewer-submit")
        self.client.force_authenticate(other_user)

        response = self.client.post("/api/inspection/submit/", {
            "batch_id": self.batch.id,
            "results": [{
                "product_item_id": self.product_item_required.id,
                "result": "PASS",
            }],
        }, format="json")

        self.assertEqual(response.status_code, 403)
        self.assertIn("errors", response.data)
