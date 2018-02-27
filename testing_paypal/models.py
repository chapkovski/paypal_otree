from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)

import random
author = 'Your name here'
from paypal_ext.models import  PPP_STATUSES
doc = """
Your app description
"""


class Constants(BaseConstants):
    name_in_url = 'testing_paypal'
    players_per_group = None
    num_rounds = 1


class Subsession(BaseSubsession):
    def creating_session(self):
        for p in self.get_players():
            p.payoff =random.randint(1,10)


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    testchoices=models.IntegerField(choices=PPP_STATUSES.choices)
