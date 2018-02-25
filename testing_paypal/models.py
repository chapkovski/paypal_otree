from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)


author = 'Your name here'
from paypal_ext.models import  PPP_STATUSES
doc = """
Your app description
"""

class BATCH_STATUSES(BaseConstants):
    UNPROCESSED = 0
    SUCCESS = 1
    FAILED = 2

class Constants(BaseConstants):
    name_in_url = 'testing_paypal'
    players_per_group = None
    num_rounds = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    testchoices=models.IntegerField(choices=PPP_STATUSES.choices)
