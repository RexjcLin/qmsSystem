from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from products.models import ProductInspectionItem

from .models import BatchStatus, InspectionBatch
from .serializers import PendingBatchSerializer, SubmitInspectionSerializer


class PendingBatchList(generics.ListAPIView):
    serializer_class = PendingBatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            InspectionBatch.objects.filter(status__in=[BatchStatus.PENDING, BatchStatus.INSPECTING])
            .select_related("product")
            .order_by("created_at")
        )


class ProductInspectionItemList(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, product_id):
        links = ProductInspectionItem.objects.filter(product_id=product_id).select_related("item").prefetch_related("item__options")
        return Response(
            [
                {
                    "product_item_id": link.id,
                    "item_id": link.item_id,
                    "item_name": link.item.name,
                    "inspection_type": link.inspection_type,
                    "method": link.inspection_method,
                    "unit": link.item.unit,
                    "standard_min": link.standard_min,
                    "standard_max": link.standard_max,
                    "standard_value": link.standard_value,
                    "is_required": link.is_required,
                    "sort_order": link.sort_order,
                    "options": [
                        {"value": option.value, "label": option.label}
                        for option in link.item.options.all()
                    ],
                }
                for link in links
            ]
        )


class SubmitInspection(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SubmitInspectionSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        record = serializer.save()
        return Response({"inspection_id": record.id, "overall_result": record.overall_result}, status=status.HTTP_201_CREATED)
