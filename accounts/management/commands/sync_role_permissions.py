from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import Role, User
from accounts.rbac import ROLE_LABELS, configure_role_groups, sync_user_role


class Command(BaseCommand):
    help = "Configure QMS role groups and synchronize existing users without changing passwords."

    @transaction.atomic
    def handle(self, *args, **options):
        configure_role_groups()
        for code, label in ROLE_LABELS.items():
            role, _ = Role.objects.get_or_create(name=code, defaults={"display_name": label})
            if not role.display_name:
                role.display_name = label
                role.save(update_fields=["display_name"])
        count = 0
        for user in User.objects.select_related("role"):
            sync_user_role(user)
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Configured 3 role groups and synchronized {count} users. Passwords unchanged."))