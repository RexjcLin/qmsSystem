from django.contrib.auth.models import AbstractUser
from django.db import models


class RoleChoices(models.TextChoices):
    ADMIN = "ADMIN", "系統管理員"
    QUALITY_MANAGER = "QUALITY_MANAGER", "品質主管"
    INSPECTOR = "INSPECTOR", "檢驗人員"


class UserStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "啟用"
    INACTIVE = "INACTIVE", "停用"


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True, choices=RoleChoices.choices)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "roles"
        ordering = ["name"]

    def __str__(self):
        return self.name


class User(AbstractUser):
    full_name = models.CharField(max_length=100, blank=True)
    role = models.ForeignKey(Role, null=True, blank=True, on_delete=models.PROTECT, related_name="users")
    status = models.CharField(max_length=10, choices=UserStatus.choices, default=UserStatus.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users"
        indexes = [models.Index(fields=["role", "status"])]

    def save(self, *args, **kwargs):
        self.is_active = self.status == UserStatus.ACTIVE
        super().save(*args, **kwargs)

    def __str__(self):
        return self.full_name or self.username
