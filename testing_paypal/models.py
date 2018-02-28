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

from django import forms as djforms
class Player(BasePlayer):
    consent = models.BooleanField(widget=djforms.CheckboxInput,
                                  initial=False
                                  )
    gender = models.CharField(verbose_name='Gender', choices=['Male', 'Female', 'Other'],
                              widget=widgets.RadioSelectHorizontal, )
    nationality = models.CharField(verbose_name='Nationality', choices=['US', 'Other'],
                                   widget=widgets.RadioSelectHorizontal, )
    nationality_other = models.CharField(verbose_name='', blank=True)
    race_ethnicity = models.CharField(verbose_name='Race/Ethnicity',
                                      choices=['African American/African/Black/Caribbean',
                                               'Asian/Pacific Islander',
                                               'Caucasian',
                                               'Hispanic/Latino',
                                               'Native American',
                                               'Other',
                                               'Prefer not to answer '
                                               ],
                                      widget=widgets.RadioSelect, )


    year_in_college = models.CharField(verbose_name='If you are currently in school, what year are you in?', choices=[
        'Freshman/First-Year ',
        'Sophomore',
        'Junior',
        'Senior',
        'Graduate Student',
        'Other'
    ],
                                       blank=True)