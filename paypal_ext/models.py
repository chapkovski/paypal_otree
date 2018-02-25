from django.db import models as djmodels
from otree.api import models
from random import randint
import string

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
    error_message = models.LongStringField(blank=True, null=True, doc='to store errors from paypal')
    info = models.LongStringField(doc='to store info received from paypal.get()')
    batch_status = models.StringField(doc='an extenral status received from paypal')
    total_amount = models.FloatField(doc='total amount of batch (taken from paypal.get()')

    def update_status(self, info):
        self.info = info
        print('QQQQ', info)
        header = info['batch_header']
        items = info['items']
        self.batch_status = header['batch_status']
        self.total_amount = float(header['amount']['value'])
        for item in items:
            payout_item_id = item['payout_item_id']
            transaction_status = item['transaction_status']
            email = item['payout_item']['receiver']
            sender_item_id = item['payout_item']['sender_item_id']
            self.payouts.filter(email=email,
                                sender_item_id=sender_item_id).update(transaction_status=transaction_status,
                                                                      payout_item_id=payout_item_id)

    # TODO: add the field Body to store the request to send to paypal
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
    batch = djmodels.ForeignKey(to=Batch, on_delete=djmodels.CASCADE, blank=True, null=True)
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
