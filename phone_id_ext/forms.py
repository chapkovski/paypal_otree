import django.forms as forms
from .models import LinkedSession, PhoneRecord
from otree.models import Session
from django.core.exceptions import ObjectDoesNotExist


class SessionChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        print('AAAA', obj)
        return obj.code


class SessionCreateForm(forms.ModelForm):
    class Meta:
        model = LinkedSession
        fields = ['session']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['session'].queryset = Session.objects.filter(linkedsession__isnull=True, is_demo=False)
        self.fields['session'].label_from_instance = lambda obj: 'code {}'.format(obj.code)


class PhoneIdlLookupForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['phone_id'] = forms.IntegerField()

    def is_valid(self):
        valid = super().is_valid()
        if not valid:
            return valid
        try:
            phone_record = PhoneRecord.objects.get(phone_id=self.cleaned_data['phone_id'])
        except ObjectDoesNotExist:
            self.add_error('phone_id',
                           "Der Code, den Sie eingegeben haben, ist nicht korrekt. Bitte versuchen Sie es noch einmal.")
            return False

        return True
