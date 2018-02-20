from . import models
import vanilla
from django.core.urlresolvers import reverse, reverse_lazy
from .forms import SessionCreateForm, PhoneIdlLookupForm
from django.views.generic.edit import CreateView
from django.http import HttpResponse
import csv
class CreateLinkedSessionView(CreateView):
    model = models.LinkedSession
    form_class = SessionCreateForm
    template_name = 'phone_id_ext/LinkedSessionCreate.html'
    success_url = reverse_lazy('linked_sessions_list')


# to delete linked session
class DeleteLinkedSessionView(vanilla.DeleteView):
    model = models.LinkedSession
    template_name = 'phone_id_ext/LinkedSessionDelete.html'
    success_url = reverse_lazy('linked_sessions_list')


# view to show linked session
class ListLinkedSessionsView(vanilla.ListView):
    template_name = 'phone_id_ext/LinkedSessionList.html'
    url_name = 'linked_sessions_list'
    url_pattern = r'^linked_sessions/$'
    display_name = 'Linked sessions management for Phone surveys'
    model = models.LinkedSession


class ListPhoneRecordsView(vanilla.ListView):
    model = models.PhoneRecord
    template_name = 'phone_id_ext/PhoneRecordsList.html'

    def get_queryset(self):
        linked_session_pk = self.kwargs['lsession']
        linked_session = models.LinkedSession.objects.get(pk=linked_session_pk)
        return linked_session.phonerecords.all()


class PhoneIdlLookupView(vanilla.FormView):
    form_class = PhoneIdlLookupForm
    template_name = 'phone_id_ext/phone_id_lookup.html'

    def form_invalid(self, form):

        response = super().form_invalid(form)
        return response

    def form_valid(self, form):
        self.phoneid = form.cleaned_data['phone_id']
        PEL = models.PhoneRecord.objects.get(phone_id=self.phoneid)
        PEL.taken = True
        PEL.save()
        self.success_url = PEL.get_absolute_url()
        return super().form_valid(form)


class CSVResponseMixin(object):
    csv_filename = 'all_linked_phone_records.csv'

    def get_csv_filename(self):
        return self.csv_filename

    def render_to_csv(self, data):
        response = HttpResponse(content_type='text/csv')
        cd = 'attachment; filename="{0}"'.format(self.get_csv_filename())
        response['Content-Disposition'] = cd

        writer = csv.writer(response)
        for row in data:
            writer.writerow(row)
        return response

class ExportLinkedDataView(CSVResponseMixin, vanilla.View):

    def get(self, request, *args, **kwargs):
        data = models.PhoneRecord.objects.all().values_list('phone_id', )
        return self.render_to_csv(data)