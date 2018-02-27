import django.forms as forms
from .models import LinkedSession, PayPalPayout, PPP_STATUSES
from otree.models import Session
from django.core.exceptions import ObjectDoesNotExist
from django.forms import inlineformset_factory

from django.core.validators import MinValueValidator, MaxValueValidator


class SessionChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.code


class SessionCreateForm(forms.ModelForm):
    class Meta:
        model = LinkedSession
        fields = ['session']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # TODO: don't foget to filter out demo session later
        self.fields['session'].queryset = Session.objects.filter(linkedsession__isnull=True)

        self.fields['session'].label_from_instance = lambda obj: 'session {} ({}, n={})'.format(obj.code,
                                                                                                obj.config[
                                                                                                    'display_name'],
                                                                                                obj.num_participants)


class EmptyForm(forms.Form):
    ...


class PPPUpdateForm(forms.ModelForm):
    class Meta:
        model = PayPalPayout
        fields = ['email', 'amount']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['amount'].required = True
        self.fields['amount'].widget.attrs['min'] = 0
        # theoretically we can process an unlimited amount via paypal but let's be reasonable
        self.fields['amount'].widget.attrs['max'] = 100
        self.fields['amount'].validators = [MinValueValidator(0), MaxValueValidator(100)]


class PPPPayForm(forms.ModelForm):
    class Meta:
        model = PayPalPayout
        fields = ['to_pay']
        widgets = {
            'to_pay': forms.CheckboxInput(),
        }

    def check_conditions(self, obj):
        if obj.email in (None, ''):
            return
        if obj.amount is None:
            return
        if obj.inner_status is not PPP_STATUSES.UNPAID:
            return

        return True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        self.fields['to_pay'].widget.attrs['class'] = 'to_pay'
        if not self.check_conditions(instance):
            self.fields['to_pay'].disabled = True

    def clean(self):
        super().clean()
        obj = self.instance
        if not self.check_conditions(obj) and 'to_pay' in self.changed_data:
            self.add_error('to_pay', 'Something is wrong with this payment!')


PPPFormSet = inlineformset_factory(LinkedSession, PayPalPayout, form=PPPPayForm, extra=0,
                                   can_delete=False)
