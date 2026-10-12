from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import APIException
from django.utils.translation import gettext_lazy as _
from defects.models import DefectRecord, DefectType
from .models import BatchStatus, InspectionBatch, InspectionRecord, InspectionResult, ResultStatus
from products.models import ProductInspectionItem


class PendingBatchSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    class Meta:
        model = InspectionBatch
        fields = ["id", "code", "product", "product_name", "quantity", "status", "assigned_inspector"]


class InspectionResultInputSerializer(serializers.Serializer):
    product_item_id = serializers.IntegerField()
    measured_value = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    result = serializers.ChoiceField(choices=["PASS", "FAIL", "NA"])
    remark = serializers.CharField(required=False, allow_blank=True)


class SubmitInspectionSerializer(serializers.Serializer):
    batch_id = serializers.IntegerField()
    remark = serializers.CharField(required=False, allow_blank=True)
    results = InspectionResultInputSerializer(many=True)

    def _validate_batch(self, batch):
        if batch.status == BatchStatus.CANCELLED:
            raise serializers.ValidationError({"batch_id": "已取消的批次不可提交檢驗結果。"})
        if batch.status == BatchStatus.COMPLETED:
            raise serializers.ValidationError({"batch_id": "此批次已完成檢驗，不可重複提交。"})
        if batch.assigned_inspector_id and batch.assigned_inspector_id != self.context["request"].user.pk:
            raise serializers.ValidationError({"batch_id": "此批次已由其他人員開始檢驗。"})

    def validate(self, attrs):
        try:
            batch = InspectionBatch.objects.select_related("product").get(pk=attrs["batch_id"])
        except InspectionBatch.DoesNotExist:
            raise serializers.ValidationError({"batch_id": _("Inspection batch was not found.")})

        self._validate_batch(batch)

        links = ProductInspectionItem.objects.filter(product=batch.product).select_related("item")
        product_items = {link.id: link for link in links}
        if not product_items:
            raise serializers.ValidationError({"batch_id": "此產品尚未設定檢驗項目。"})
        required_ids = {link.id for link in links if link.is_required}
        sent = [item["product_item_id"] for item in attrs["results"]]
        if len(sent) != len(set(sent)):
            raise serializers.ValidationError({"results": "同一產品檢驗項目不可重複。"})
        if not set(sent).issubset(product_items):
            raise serializers.ValidationError({"results": "包含不屬於此批次產品的檢驗項目。"})

        missing_required = sorted(required_ids - set(sent))
        if missing_required:
            raise serializers.ValidationError({
                "results": "所有必填檢驗項目都必須提交。",
                "missing_required_product_item_ids": missing_required,
            })

        required_na_ids = sorted(
            row["product_item_id"]
            for row in attrs["results"]
            if product_items[row["product_item_id"]].is_required and row["result"] == ResultStatus.NA
        )
        if required_na_ids:
            raise serializers.ValidationError({
                "results": "必填檢驗項目不可標記為 NA。",
                "required_na_product_item_ids": required_na_ids,
            })

        if not attrs["results"] or all(row["result"] == ResultStatus.NA for row in attrs["results"]):
            raise serializers.ValidationError({"results": "至少需要一項有效的檢驗結果。"})
        for row in attrs["results"]:
            item = product_items[row["product_item_id"]].item
            if row["result"] == ResultStatus.NA:
                continue
            value = row.get("measured_value")
            if item.standard_min is not None or item.standard_max is not None:
                if value is None:
                    raise serializers.ValidationError({"results": f"{item.name} 必須輸入量測值。"})
                out_of_range = (
                    item.standard_min is not None and value < item.standard_min
                    or item.standard_max is not None and value > item.standard_max
                )
                if out_of_range and row["result"] == ResultStatus.PASS:
                    raise serializers.ValidationError({"results": f"{item.name} 的量測值超出規格，不可標記為 PASS。"})

        attrs["product_items"] = product_items
        attrs["batch"] = batch
        return attrs

    def _calculate_overall_result(self, rows, product_items):
        if any(row["result"] == "FAIL" for row in rows):
            return ResultStatus.FAIL
        return ResultStatus.PASS

    def create(self, validated_data):
        try:
            with transaction.atomic():
                batch = InspectionBatch.objects.select_for_update().select_related("product").get(pk=validated_data["batch"].pk)
                validated_data = self.validate({
                    "batch_id": batch.pk,
                    "results": validated_data["results"],
                    "remark": validated_data.get("remark", ""),
                })

                batch.status = BatchStatus.INSPECTING
                batch.assigned_inspector = self.context["request"].user
                batch.save(update_fields=["status", "assigned_inspector", "updated_at"])

                rows = validated_data["results"]
                product_items = validated_data["product_items"]
                overall = self._calculate_overall_result(rows, product_items)
                record = InspectionRecord.objects.create(
                    batch=batch,
                    inspector=self.context["request"].user,
                    overall_result=overall,
                    remark=validated_data.get("remark", ""),
                )
                InspectionResult.objects.bulk_create([
                    InspectionResult(
                        inspection=record,
                        product_item=product_items[r["product_item_id"]],
                        measured_value=r.get("measured_value"),
                        result=r["result"],
                        standard_min_snapshot=product_items[r["product_item_id"]].item.standard_min,
                        standard_max_snapshot=product_items[r["product_item_id"]].item.standard_max,
                        inspection_method_snapshot=product_items[r["product_item_id"]].item.inspection_method,
                        unit_snapshot=product_items[r["product_item_id"]].item.unit,
                        remark=r.get("remark", ""),
                    )
                    for r in rows
                ])
                failed_rows = [row for row in rows if row["result"] == ResultStatus.FAIL]
                if failed_rows:
                    defect_type, _ = DefectType.objects.get_or_create(
                        name="Inspection failure", defaults={"description": "Nonconformance reported during inspection."},
                    )
                    for row in failed_rows:
                        item = product_items[row["product_item_id"]].item
                        DefectRecord.objects.create(
                            inspection=record,
                            defect_type=defect_type,
                            reported_by=self.context["request"].user,
                            description=(
                                f"{item.name}: {row.get('measured_value')} {item.unit}; "
                                f"standard {item.standard_min} ~ {item.standard_max}. "
                                f"{row.get('remark', '')}"
                            ),
                        )
                batch.status = BatchStatus.COMPLETED
                batch.save(update_fields=["status", "updated_at"])
                return record
        except serializers.ValidationError:
            raise
        except Exception as exc:
            raise APIException("檢驗結果提交失敗。") from exc
