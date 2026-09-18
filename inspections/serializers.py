from django.db import transaction
from rest_framework import serializers

from products.models import ProductInspectionItem

from .models import (
    BatchStatus,
    InspectionBatch,
    InspectionItemResult,
    InspectionOverallResult,
    InspectionRecord,
    InspectionResult,
)


class PendingBatchSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = InspectionBatch
        fields = ["id", "code", "product", "product_name", "quantity", "status"]


class InspectionResultInputSerializer(serializers.Serializer):
    product_item_id = serializers.IntegerField()
    measured_value = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    measured_text = serializers.CharField(required=False, allow_blank=True)
    result = serializers.ChoiceField(choices=[InspectionItemResult.PASS, InspectionItemResult.FAIL, InspectionItemResult.NA])
    remark = serializers.CharField(required=False, allow_blank=True)


class SubmitInspectionSerializer(serializers.Serializer):
    batch_id = serializers.IntegerField()
    remark = serializers.CharField(required=False, allow_blank=True)
    results = InspectionResultInputSerializer(many=True)

    def validate(self, attrs):
        try:
            batch = InspectionBatch.objects.select_related("product").get(pk=attrs["batch_id"])
        except InspectionBatch.DoesNotExist as exc:
            raise serializers.ValidationError({"batch_id": "找不到檢驗批次。"}) from exc

        if batch.status not in {BatchStatus.PENDING, BatchStatus.INSPECTING}:
            raise serializers.ValidationError({"batch_id": "此批次目前不可送出檢驗結果。"})

        product_items = ProductInspectionItem.objects.filter(product=batch.product)
        permitted = set(product_items.values_list("id", flat=True))
        required = set(product_items.filter(is_required=True).values_list("id", flat=True))
        sent = [item["product_item_id"] for item in attrs["results"]]
        if len(sent) != len(set(sent)):
            raise serializers.ValidationError({"results": "同一產品檢驗項目不可重複。"})
        if not set(sent).issubset(permitted):
            raise serializers.ValidationError({"results": "包含不屬於此產品的檢驗設定。"})
        if not required.issubset(sent):
            raise serializers.ValidationError({"results": "必要檢驗項目尚未完成。"})

        attrs["batch"] = batch
        attrs["product_items"] = {
            product_item.id: product_item for product_item in product_items.select_related("item")
        }
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        batch = InspectionBatch.objects.select_for_update().select_related("product").get(pk=validated_data["batch"].pk)
        if batch.status not in {BatchStatus.PENDING, BatchStatus.INSPECTING}:
            raise serializers.ValidationError({"batch_id": "此批次目前不可送出檢驗結果。"})
        rows = validated_data["results"]
        required_item_ids = {
            product_item_id
            for product_item_id, product_item in validated_data["product_items"].items()
            if product_item.is_required
        }
        row_map = {row["product_item_id"]: row for row in rows}
        if any(row_map[product_item_id]["result"] == InspectionItemResult.FAIL for product_item_id in required_item_ids):
            overall = InspectionOverallResult.FAIL
        elif required_item_ids.issubset(row_map.keys()):
            overall = InspectionOverallResult.PASS
        else:
            overall = InspectionOverallResult.PENDING

        record = InspectionRecord.objects.create(
            batch=batch,
            inspector=self.context["request"].user,
            overall_result=overall,
            remark=validated_data.get("remark", ""),
        )
        for row in rows:
            InspectionResult.objects.create(
                inspection=record,
                product_inspection_item=validated_data["product_items"][row["product_item_id"]],
                measured_value=row.get("measured_value"),
                measured_text=row.get("measured_text", ""),
                result=row["result"],
                remark=row.get("remark", ""),
                inspection_type_snapshot="",
            )
        batch.status = BatchStatus.COMPLETED if overall != InspectionOverallResult.PENDING else BatchStatus.INSPECTING
        batch.save(update_fields=["status", "updated_at"])
        return record
