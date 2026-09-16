from django.contrib import admin
from .models import CorrectiveAction, DefectImage, DefectRecord, DefectType
admin.site.register([DefectType, DefectRecord, DefectImage, CorrectiveAction])
