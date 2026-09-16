from django.contrib import admin
from .models import InspectionBatch, InspectionRecord, InspectionResult
admin.site.register([InspectionBatch, InspectionRecord, InspectionResult])
