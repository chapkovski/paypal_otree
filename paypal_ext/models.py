from django.db import models as djmodels
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from otree.api import models
from random import randint
import string
import paypal_ext.paypal as paypal
import json
import ast

author = 'Philip Chapkovski'

doc = """
Extention to deal with phone records
"""

from otree.models import Participant, Session
import random
from django.db.models.signals import post_save
from django.dispatch import receiver
from otree.constants import BaseConstants
from django.core.exceptions import ObjectDoesNotExist

# if a batch has one of these statuses, we don't update them anymore requesting info
# via paypal, because it doesn't make sense, they are finalized.
# TODO: NB! correct it after debugging
# TODO: the problem with this approach is that status of batch can be success, but statuses of payout items can
# TODO: change later: from unclaimed to paid, or returned
BATCH_IGNORED_STATUSES = ['1SUCCESS', '1DENIED']
PPP_IGNORED_STATUSES = ['1SUCCESS', '1DENIED']


def generate_random_string(stringlength=12):
    rstring = ''.join(
        random.choice(string.ascii_uppercase) for i in range(stringlength))
    return rstring


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

    @property
    def choices(self):
        return [(v, k) for k, v in self.items()]


ppp_statuses_dict = {
    'UNPAID': 0,
    'PAID': 1,
    'PROCESSING': 2,
}
batch_statutses_dict = {
    'UNPROCESSED': 0,
    'SUCCESS': 1,
    'FAILED': 2,
}
PPP_STATUSES = AttrDict(ppp_statuses_dict)
BATCH_STATUSES = AttrDict(batch_statutses_dict)


# Models for phone identification
class LinkedSession(djmodels.Model):
    session = djmodels.OneToOneField(to=Session, on_delete=djmodels.CASCADE)

    @property
    def total_amount(self):
        return sum([p.payoff_in_real_world_currency() for p in self.session.get_participants()])

    @property
    def num_parts(self):
        return len(self.session.get_participants())

    @property
    def payment_processed(self):
        return self.batch_set.exists()


class FailedBatch(djmodels.Model):
    error_message = models.LongStringField(blank=True, null=True, doc='to store errors from paypal')
    error_level = models.StringField(doc='to store level of failure (see payout.create() for details')


class Batch(djmodels.Model):
    email_subject = models.StringField()
    email_message = models.StringField()
    sender_batch_id = models.StringField()
    payout_batch_id = models.StringField(null=True,
                                         blank=True,
                                         doc='to keep the response from Paypal.'
                                             'extremely important because it is pain in the ass'
                                             'to get the list of payout batches (impossible via'
                                             'current api afaik')
    batch_body = models.LongStringField(doc='to store the entire batch body just in case',
                                        blank=True,
                                        null=True)
    inner_status = models.IntegerField(choices=BATCH_STATUSES.choices,
                                       default=BATCH_STATUSES.UNPROCESSED)
    linked_session = djmodels.ForeignKey(to=LinkedSession, on_delete=djmodels.CASCADE, )

    info = models.LongStringField(doc='to store info received from paypal.get()')
    batch_status = models.StringField(doc='an extenral status received from paypal')
    total_amount = models.FloatField(doc='total amount of batch (taken from paypal.get()')
    total_items = models.IntegerField(doc='total number of items (taken from paypal.get()')
    total_fees = models.FloatField(doc='total amount of fees (taken from paypal.get()')

    def update_status(self):
        if self.payout_batch_id == '':
            return False
        if self.batch_status not in BATCH_IGNORED_STATUSES:
            info = paypal.get(self.payout_batch_id)

            if 'error_status' not in info:
                self.info = json.dumps(info)
                header = info['batch_header']
                items = info['items']
                self.batch_status = header['batch_status']
                self.total_amount = float(header['amount']['value'])
                self.total_fees = float(header['fees']['value'])
                self.total_items = len(items)
                self.save()
                for item in items:
                    payout_item_id = item['payout_item_id']
                    transaction_status = item['transaction_status']
                    email = item['payout_item']['receiver']
                    sender_item_id = item['payout_item']['sender_item_id']
                    self.payouts.filter(email=email,
                                        sender_item_id=sender_item_id).update(transaction_status=transaction_status,
                                                                              payout_item_id=payout_item_id,
                                                                              info=item)

                return True
            else:
                return False

    # TODO: add the field inner_status to distinguish between non-sent, failed, and succesffuly sent batches


    def get_payout_header(self):
        return {
            "sender_batch_id": self.sender_batch_id,
            "email_subject": self.email_subject,
            'email_message': self.email_message,
        }

    def get_payout_items(self):
        return [i.get_payout_item() for i in self.payouts.all()]

    def get_payout_body_of_batch(self, items):
        header = self.get_payout_header()

        payout = {
            "sender_batch_header": header,
            "items": items,
        }
        return payout


class PayPalPayout(djmodels.Model):
    class Meta:
        default_related_name = 'payouts'

    linked_session = djmodels.ForeignKey(to=LinkedSession, on_delete=djmodels.CASCADE, )
    participant = djmodels.ForeignKey(to=Participant, on_delete=djmodels.CASCADE, )
    # we set on_delete to NULL because we need to delete failed batches without touching ppp object connected.
    batch = djmodels.ForeignKey(to=Batch, on_delete=djmodels.SET_NULL, blank=True, null=True)
    email = djmodels.EmailField(blank=True, )
    amount = models.FloatField(blank=True, null=True)
    payout_item_id = models.StringField(blank=True, doc='returned id from paypal.get()')
    inner_status = models.IntegerField(choices=PPP_STATUSES.choices, blank=True, null=True,
                                       initial=PPP_STATUSES.UNPAID)
    transaction_status = models.StringField(blank=True, initial='NOT PAID', doc='to get from paypal.get()')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    to_pay = models.BooleanField(doc='Marked as to pay, but not yet processed, inner status = PROCESSING',
                                 initial=False)
    paid = models.BooleanField(doc='paid, inner status PAID',
                               initial=False)
    sender_item_id = models.StringField(blank=True, doc='sent id to paypal', )
    info = models.LongStringField(doc='to store info received from paypal.get_payout()')

    def get_absolute_url(self):
        return self.participant._url_i_should_be_on()

    def get_payout_item(self):
        self.sender_item_id = generate_random_string(15)
        if self.email is None:
            return
        if self.amount is None:
            return
        return {
            "recipient_type": "EMAIL",
            "amount": {
                "value": self.amount,
                "currency": "USD"
            },
            "receiver": self.email,
            "note": "Thank you.",
            "sender_item_id": self.sender_item_id
        }

    def update_status(self):
        if self.payout_item_id == '':
            return False
        if self.transaction_status not in PPP_IGNORED_STATUSES:
            updated_info = paypal.get_payout_item(self.payout_item_id)
            if 'error_status' not in updated_info:
                self.info = str(updated_info)
                self.transaction_status = updated_info['transaction_status']
                self.save()
                return True
            else:
                return False


# This is to guarantee that linked session will never be deleted if there is at least one ppp in status **NOT**
# Not Paid. Using signals presumably more safe than override delete method on LinkedSession model because bulk_delete
# does not call delete method (god knows if this is worth the efforts - who uses bulk delete after alL? but JIC)


class PaidPPPExistsException(Exception):
    pass


@receiver(pre_delete, sender=LinkedSession)
def check_if_ppp_paid(sender, instance, *args, **kwargs):
    for p in instance.payouts.all():
        if p.transaction_status != 'NOT PAID':
            raise PaidPPPExistsException('Can\'t delete the linked session with the processed payment')

