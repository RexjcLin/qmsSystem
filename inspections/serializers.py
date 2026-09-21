from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import InspectionBatch, InspectionRecord, InspectionResult
from products.models import ProductInspectionItem


class PendingBatchSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    class Meta:
        model = InspectionBatch
        fields = ["id", "code", "product", "product_name", "quantity", "status"]


class InspectionResultInputSerializer(serializers.Serializer):
    item_id = serializers.IntegerField()
    measured_value = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    result = serializers.ChoiceField(choices=["PASS", "FAIL", "NA"])
    remark = serializers.CharField(required=False, allow_blank=True)


class SubmitInspectionSerializer(serializers.Serializer):
    batch_id = serializers.IntegerField()
    remark = serializers.CharField(required=False, allow_blank=True)
    results = InspectionResultInputSerializer(many=True)

    def validate(self, attrs):
        try: batch = InspectionBatch.objects.select_related("product").get(pk=attrs["batch_id"])
        except InspectionBatch.DoesNotExist: raise serializers.ValidationError({"batch_id": _("Inspection batch was not found.")})
        permitted = set(ProductInspectionItem.objects.filter(product=batch.product).values_list("item_id", flat=True))
        sent = [item["item_id"] for item in attrs["results"]]
        if len(sent) != len(set(sent)): raise serializers.ValidationError({"results": _("Duplicate inspection items are not allowed.")})
        if not set(sent).issubset(permitted): raise serializers.ValidationError({"results": _("Results contain inspection items that do not belong to this product.")})
        attrs["batch"] = batch
        return attrs

    def create(self, validated_data):
        batch = validated_data["batch"]
        rows = validated_data["results"]
        overall = "FAIL" if any(r["result"] == "FAIL" for r in rows) else "PASS"
        record = InspectionRecord.objects.create(batch=batch, inspector=self.context["request"].user, overall_result=overall, remark=validated_data.get("remark", ""))
        InspectionResult.objects.bulk_create([InspectionResult(inspection=record, item_id=r["item_id"], measured_value=r.get("measured_value"), result=r["result"], remark=r.get("remark", "")) for r in rows])
        batch.status = "COMPLETED"
        batch.save(update_fields=["status", "updated_at"])
        return record
