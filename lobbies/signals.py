import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from appsettings.services import is_restriction_on

from .models import PlayerDodges, PlayerRestriction
from .tasks import end_player_restriction


@receiver(post_save, sender=PlayerDodges)
def apply_player_restriction(sender, instance: PlayerDodges, **kwargs):
    if not is_restriction_on():
        return

    dodges_to_restrict = settings.PLAYER_DODGES_MIN_TO_RESTRICT
    dodges_multipliers = settings.PLAYER_DODGES_MULTIPLIER

    if instance.count >= dodges_to_restrict:
        logging.info(
            f'[apply_player_restriction] user {instance.user.id} dodges {instance.count} times'
        )
        factor_idx = instance.count - dodges_to_restrict
        if factor_idx > len(dodges_multipliers):
            factor_idx = len(dodges_multipliers) - 1

        factor = dodges_multipliers[factor_idx]
        lock_minutes = instance.count * factor
        delta = timezone.timedelta(minutes=lock_minutes)
        restriction_end_date = timezone.now() + delta
        logging.info(
            f'[apply_player_restriction] factor {factor} lock_minutes {lock_minutes}'
        )

        if hasattr(instance.user, 'playerrestriction'):
            restriction = instance.user.playerrestriction
            restriction.end_date = restriction_end_date
            restriction.save()
        else:
            restriction = PlayerRestriction.objects.create(
                user=instance.user,
                reason=PlayerRestriction.Reason.DODGES,
                start_date=timezone.now(),
                end_date=restriction_end_date,
            )

        restriction.refresh_from_db()
        logging.info(
            f'[apply_player_restriction] restriction end date {restriction.end_date}'
        )

        end_player_restriction.apply_async(
            (restriction.user.id,),
            eta=restriction.end_date,
            serializer='json',
        )
