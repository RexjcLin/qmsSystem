from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.utils.translation import gettext_lazy as _
from dashboard.views import dashboard

admin.site.site_header = _("QMS Administration")
admin.site.site_title = _("QMS Admin")
admin.site.index_title = _("Site administration")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", dashboard, name="dashboard"),
    path("i18n/", include("django.conf.urls.i18n")),
    path("api/", include("inspections.urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
