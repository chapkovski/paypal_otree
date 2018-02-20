from django.db import models as djmodels
from otree.api import models
from random import randint

author = 'Philip Chapkovski'

doc = """
Extention to deal with phone records
"""

from otree.models import Participant, Session
import random
from django.db.models.signals import post_save
from django.dispatch import receiver


# Models for phone identification
class LinkedSession(djmodels.Model):
    session = djmodels.OneToOneField(to=Session, on_delete=djmodels.CASCADE)


class PhoneRecord(djmodels.Model):
    phone_id = djmodels.BigIntegerField(unique=True)
    # 'link to the session'
    linked_session = djmodels.ForeignKey(to=LinkedSession,
                                         on_delete=djmodels.CASCADE,
                                         related_name='phonerecords',
                                         )
    # 'link to the participant and his correspoinding url'
    participant = djmodels.ForeignKey(to=Participant, on_delete=djmodels.CASCADE, )
    taken = models.BooleanField(default=False, doc='to check whether the record was already used')

    def get_absolute_url(self):
        return self.participant._url_i_should_be_on()


@receiver(post_save, sender=LinkedSession)
def create_linked_session(sender, instance, created, **kwargs):
    if created:
        q_to_add = len(instance.session.get_participants())
        existing_nums = PhoneRecord.objects.all().values_list('phone_id', flat=True)
        n_to_choose_from = list(set(range(10 ** 4, 10 ** 5)) - set(existing_nums))
        n_to_add = random.sample(n_to_choose_from, q_to_add)
        objs = [
            PhoneRecord(
                linked_session=instance,
                participant=p,
                phone_id=n_to_add[i],
            )
            for i, p in enumerate(instance.session.get_participants())
        ]
        obj = PhoneRecord.objects.bulk_create(objs)
