from django.urls import path
from .views import PendingBatchList, ProductInspectionItemList, SubmitInspection
urlpatterns = [
    path("inspection/pending/", PendingBatchList.as_view()),
    path("products/<int:product_id>/inspection-items/", ProductInspectionItemList.as_view()),
    path("inspection/submit/", SubmitInspection.as_view()),
]
