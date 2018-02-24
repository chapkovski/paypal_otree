import django.forms as forms
from .models import LinkedSession, PayPalPayout
from otree.models import Session
from django.core.exceptions import ObjectDoesNotExist
from django.forms import inlineformset_factory


class SessionChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.code


class SessionCreateForm(forms.ModelForm):
    class Meta:
        model = LinkedSession
        fields = ['session']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #TODO: don't foget to filter out demo session later
        self.fields['session'].queryset = Session.objects.filter(linkedsession__isnull=True)
        self.fields['session'].label_from_instance = lambda obj: 'code {}'.format(obj.code)


class EmptyForm(forms.Form):
    ...


class PPPUpdateForm(forms.ModelForm):
    class Meta:
        model = PayPalPayout
        fields = ['to_pay']
        widgets = {
            'to_pay': forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        #TODO: uncomment later
        # if instance.to_pay:
        #     self.fields['to_pay'].disabled = True
        if instance.email in (None,''):
            self.fields['to_pay'].disabled = True


PPPFormSet = inlineformset_factory(LinkedSession, PayPalPayout, form=PPPUpdateForm, extra=0,
                                   can_delete=False)
