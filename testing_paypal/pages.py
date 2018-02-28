from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import Constants


class Consent(Page):
    form_model = 'player'
    form_fields = ['consent']

    def consent_error_message(self, value):
        if not value:
            return 'You must accept the consent form'


class Survey(Page):
    form_model = 'player'
    form_fields = [
        'gender',
        'nationality',
        'race_ethnicity',
        'year_in_college',
    ]


page_sequence = [
    Consent,
    Survey
]
