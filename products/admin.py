from django.contrib import admin
from .models import ProductCategory, Product, InspectionItem, ProductInspectionItem
admin.site.register([ProductCategory, Product, InspectionItem, ProductInspectionItem])
