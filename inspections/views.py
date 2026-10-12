from django.db import transaction
from django.db.models import Q
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.permissions import CanAccessInspectionAPI
from products.models import ProductInspectionItem
from .models import BatchStatus, InspectionBatch
from .serializers import PendingBatchSerializer, SubmitInspectionSerializer


class PendingBatchList(generics.ListAPIView):
    serializer_class = PendingBatchSerializer
    permission_classes = [CanAccessInspectionAPI]
    required_permissions = ("inspections.view_inspectionbatch",)
    def get_queryset(self):
        batches = InspectionBatch.objects.filter(status__in=[BatchStatus.PENDING, BatchStatus.INSPECTING])
        user = self.request.user
        if not user.is_superuser and user.role.name == "INSPECTOR":
            batches = batches.filter(Q(assigned_inspector=user) | Q(assigned_inspector__isnull=True))
        return batches.select_related("product").order_by("created_at")


class InspectionBatchAction(APIView):
    permission_classes = [CanAccessInspectionAPI]
    required_permissions = ("inspections.change_inspectionbatch",)

    @transaction.atomic
    def post(self, request, batch_id, action):
        try:
            batch = InspectionBatch.objects.select_for_update().get(pk=batch_id)
        except InspectionBatch.DoesNotExist:
            raise NotFound("找不到檢驗批次。")
        if batch.status not in (BatchStatus.PENDING, BatchStatus.INSPECTING):
            raise ValidationError({"batch_id": "已完成或取消的批次不可開始或釋放檢驗。"})
        owner_matches = batch.assigned_inspector_id in (None, request.user.pk)
        can_release_others = request.user.is_superuser or request.user.role.name in ("ADMIN", "QUALITY_MANAGER")
        if not owner_matches and not (action == "release" and can_release_others):
            raise PermissionDenied("此批次已由其他人員開始檢驗。")
        if action == "start":
            if not batch.product.inspection_item_links.exists():
                raise ValidationError({"batch_id": "此產品尚未設定檢驗項目。"})
            batch.status = BatchStatus.INSPECTING
            batch.assigned_inspector = request.user
        else:
            if batch.status != BatchStatus.INSPECTING:
                raise ValidationError({"batch_id": "此批次尚未開始檢驗。"})
            batch.status = BatchStatus.PENDING
            batch.assigned_inspector = None
        batch.save(update_fields=["status", "assigned_inspector", "updated_at"])
        return Response(PendingBatchSerializer(batch).data)


class ProductInspectionItemList(APIView):
    permission_classes = [CanAccessInspectionAPI]
    required_permissions = ("products.view_productinspectionitem",)
    def get(self, request, product_id):
        links = ProductInspectionItem.objects.filter(product_id=product_id).select_related("item")
        return Response([{ "product_item_id": x.id, "item_id": x.item_id, "item_name": x.item.name, "method": x.item.inspection_method, "unit": x.item.unit, "standard_min": x.item.standard_min, "standard_max": x.item.standard_max, "is_required": x.is_required } for x in links])


class SubmitInspection(APIView):
    permission_classes = [CanAccessInspectionAPI]
    required_permissions = ("inspections.add_inspectionrecord", "inspections.add_inspectionresult")
    def post(self, request):
        serializer = SubmitInspectionSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        record = serializer.save()
        return Response({
            "inspection_id": record.id,
            "overall_result": record.overall_result,
            "defect_ids": list(record.defects.values_list("id", flat=True)),
        }, status=status.HTTP_201_CREATED)
