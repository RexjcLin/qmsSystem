from django.db.models.signals import m2m_changed, post_migrate, post_save
from django.dispatch import receiver

from .models import User
from .rbac import configure_role_groups, sync_user_role


@receiver(post_save, sender=User)
def user_saved(sender, instance, raw=False, using="default", **kwargs):
    if not raw:
        sync_user_role(instance, using=using)


@receiver(m2m_changed, sender=User.groups.through)
def user_groups_changed(sender, instance, action, reverse, pk_set, using="default", **kwargs):
    if reverse and action == "pre_clear":
        instance._role_sync_user_ids = list(instance.user_set.using(using).values_list("pk", flat=True))
    if action not in {"post_add", "post_remove", "post_clear"}:
        return
    if reverse:
        user_ids = pk_set if pk_set is not None else getattr(instance, "_role_sync_user_ids", [])
        for user in User.objects.using(using).filter(pk__in=user_ids).select_related("role"):
            sync_user_role(user, using=using)
    else:
        sync_user_role(instance, using=using)


@receiver(post_migrate)
def permissions_created(sender, using="default", **kwargs):
    configure_role_groups(using=using)