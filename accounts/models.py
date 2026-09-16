from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "roles"
    def __str__(self): return self.name


class User(AbstractUser):
    full_name = models.CharField(max_length=100, blank=True)
    role = models.ForeignKey(Role, null=True, blank=True, on_delete=models.PROTECT, related_name="users")
    status = models.CharField(max_length=10, choices=[("ACTIVE", "啟用"), ("INACTIVE", "停用")], default="ACTIVE")

    class Meta:
        db_table = "users"
    def __str__(self): return self.full_name or self.username
