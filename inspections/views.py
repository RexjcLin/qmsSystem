from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.permissions import CanAccessInspectionAPI
from products.models import ProductInspectionItem
from .models import BatchStatus, InspectionBatch
from .serializers import PendingBatchSerializer, SubmitInspectionSerializer


class PendingBatchList(generics.ListAPIView):
    serializer_class = PendingBatchSerializer
    permission_classes = [CanAccessInspectionAPI]
    def get_queryset(self):
        return InspectionBatch.objects.filter(status__in=[BatchStatus.PENDING, BatchStatus.INSPECTING]).select_related("product").order_by("created_at")


class ProductInspectionItemList(APIView):
    permission_classes = [CanAccessInspectionAPI]
    def get(self, request, product_id):
        links = ProductInspectionItem.objects.filter(product_id=product_id).select_related("item")
        return Response([{ "product_item_id": x.id, "item_name": x.item.name, "method": x.item.inspection_method, "unit": x.item.unit, "standard_min": x.item.standard_min, "standard_max": x.item.standard_max, "is_required": x.is_required } for x in links])


class SubmitInspection(APIView):
    permission_classes = [CanAccessInspectionAPI]
    def post(self, request):
        serializer = SubmitInspectionSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        record = serializer.save()
        return Response({"inspection_id": record.id, "overall_result": record.overall_result}, status=status.HTTP_201_CREATED)
