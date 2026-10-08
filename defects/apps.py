from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DefectsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "defects"
    verbose_name = _("Defects")
