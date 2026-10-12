from django.urls import path
from .views import InspectionBatchAction, PendingBatchList, ProductInspectionItemList, SubmitInspection
urlpatterns = [
    path("inspection/pending/", PendingBatchList.as_view()),
    path("inspection/batches/<int:batch_id>/start/", InspectionBatchAction.as_view(), {"action": "start"}),
    path("inspection/batches/<int:batch_id>/release/", InspectionBatchAction.as_view(), {"action": "release"}),
    path("products/<int:product_id>/inspection-items/", ProductInspectionItemList.as_view()),
    path("inspection/submit/", SubmitInspection.as_view()),
]
