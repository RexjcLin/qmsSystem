from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class Role(models.Model):
    class Code(models.TextChoices):
        ADMIN = "ADMIN", _("Administrator")
        QUALITY_MANAGER = "QUALITY_MANAGER", _("Quality manager")
        INSPECTOR = "INSPECTOR", _("Inspector")

    name = models.CharField(max_length=50, unique=True, choices=Code.choices, verbose_name=_("Role name"))
    display_name = models.CharField(max_length=100, blank=True, verbose_name=_("Display name"))
    description = models.CharField(max_length=255, blank=True, verbose_name=_("Role description"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))

    class Meta:
        db_table = "roles"
        verbose_name = _("Role")
        verbose_name_plural = _("Roles")
    def __str__(self): return self.display_name or self.get_name_display()

    def save(self, *args, **kwargs):
        self._meta.get_field("name").clean(self.name, self)
        using = kwargs.get("using") or self._state.db or "default"
        if self.pk:
            original = type(self).objects.using(using).filter(pk=self.pk).values_list("name", flat=True).first()
            if original is not None and original != self.name:
                raise ValidationError({"name": "Role codes cannot be changed; edit the display name instead."})
        return super().save(*args, **kwargs)


class User(AbstractUser):
    full_name = models.CharField(max_length=100, blank=True, verbose_name=_("Full name"))
    role = models.ForeignKey(Role, null=True, blank=True, on_delete=models.PROTECT, related_name="users", verbose_name=_("Role"))
    status = models.CharField(max_length=10, choices=[("ACTIVE", _("Active")), ("INACTIVE", _("Inactive"))], default="ACTIVE", verbose_name=_("Status"))

    class Meta:
        db_table = "users"
        verbose_name = _("User")
        verbose_name_plural = _("Users")
    def __str__(self): return self.full_name or self.username
