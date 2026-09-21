import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from accounts.models import Role
from defects.models import CorrectiveAction, DefectRecord, DefectType
from inspections.models import BatchStatus, InspectionBatch, InspectionRecord, ResultStatus
from products.models import InspectionItem, Product


class InternationalizationTests(TestCase):
    def setUp(self):
        self.role = Role.objects.create(name="QUALITY_MANAGER", description="Quality manager")
        self.user = get_user_model().objects.create_user(
            username="inspector",
            **{"password": "secret123"},
            full_name="測試人員",
            role=self.role,
        )
        self.product = Product.objects.create(code="P-001", name="Widget", status="ACTIVE")
        self.item = InspectionItem.objects.create(name="Length")
        self.batch = InspectionBatch.objects.create(
            code="B-001",
            product=self.product,
            quantity=10,
            status=BatchStatus.PENDING,
            created_by=self.user,
        )
        self.record = InspectionRecord.objects.create(
            batch=self.batch,
            inspector=self.user,
            overall_result=ResultStatus.FAIL,
        )
        self.defect_type = DefectType.objects.create(name="Scratch", status="ACTIVE")
        self.defect = DefectRecord.objects.create(
            inspection=self.record,
            defect_type=self.defect_type,
            reported_by=self.user,
            status=DefectRecord.Status.PROCESSING,
        )
        self.corrective_action = CorrectiveAction.objects.create(
            defect=self.defect,
            action_description="Check process",
            assigned_to=self.user,
            status=CorrectiveAction.Status.PENDING,
        )

    def test_dashboard_defaults_to_traditional_chinese(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, "品質管理系統（QMS）")
        self.assertContains(response, "語言")
        self.assertContains(response, "最近異常紀錄")
        self.assertContains(response, "處理中")

    def test_switching_to_english_persists_via_language_cookie(self):
        self.client.force_login(self.user)

        switch_response = self.client.post(
            reverse("set_language"),
            {"language": "en", "next": reverse("dashboard")},
        )

        self.assertRedirects(switch_response, reverse("dashboard"))
        self.assertEqual(switch_response.cookies["django_language"].value, "en")

        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, "Quality Management System (QMS)")
        self.assertContains(response, "Recent defect records")
        self.assertContains(response, "Language")
        self.assertContains(response, "In progress")

    def test_language_redirect_rejects_open_redirect_for_anonymous_user(self):
        response = self.client.post(
            reverse("set_language"),
            {"language": "en", "next": "https://evil.example/phish"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(response["Location"].startswith("https://evil.example/"))

    def test_role_and_corrective_action_labels_translate(self):
        with translation.override("zh-hant"):
            self.assertEqual(str(Role._meta.verbose_name), "角色")
            self.assertEqual(str(CorrectiveAction._meta.verbose_name), "改善措施")
            self.assertEqual(CorrectiveAction.Status.PENDING.label, "待處理")
        with translation.override("en"):
            self.assertEqual(str(Role._meta.verbose_name), "Role")
            self.assertEqual(str(CorrectiveAction._meta.verbose_name), "Corrective action")
            self.assertEqual(CorrectiveAction.Status.PENDING.label, "Pending")

    def test_api_error_message_uses_active_language(self):
        self.client.force_login(self.user)

        zh_response = self.client.post(
            "/api/inspection/submit/",
            data=json.dumps({"batch_id": 9999, "results": []}),
            content_type="application/json",
        )
        self.assertEqual(zh_response.status_code, 400)
        self.assertEqual(zh_response.json()["batch_id"][0], "找不到檢驗批次。")

        self.client.post(reverse("set_language"), {"language": "en", "next": reverse("dashboard")})
        en_response = self.client.post(
            "/api/inspection/submit/",
            data=json.dumps({"batch_id": 9999, "results": []}),
            content_type="application/json",
        )
        self.assertEqual(en_response.status_code, 400)
        self.assertEqual(en_response.json()["batch_id"][0], "Inspection batch was not found.")
