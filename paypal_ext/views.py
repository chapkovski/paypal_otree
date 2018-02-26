from . import models, forms
import vanilla
from django.core.urlresolvers import reverse_lazy, reverse
from .forms import SessionCreateForm, PPPFormSet
from django.views.generic.edit import CreateView, FormView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from .models import (PayPalPayout as PPP, BATCH_STATUSES, PPP_STATUSES, generate_random_string, FailedBatch, Batch,
                     BATCH_IGNORED_STATUSES)
from django.db import transaction
import random
import string
import paypal_ext.conf as conf
import paypal_ext.paypal as paypal
from django.db.models import Q

debug_emails = ['chapkovksi@gmail.com', 'anna.s.ivanova@gmail.com']

'''
Description of views we need here:
* a set of CRUD for Linked sessions (already here)
* entry point (sort of already here)
* Processing payment view - with a list of PPPs (PPP stays for PayPalPayment)
* List of made Batches (ListView for Batch model). There is no C(R)UD there because we create batches when we pay for
PPPs, and it doesn't make sense to delete them.
* Ajax view to update the status of batches
* Ajax view to update the status of payments
* POST view for receiving paypal webhooks


'''


class CreateLinkedSessionView(CreateView):
    model = models.LinkedSession
    form_class = SessionCreateForm
    template_name = 'paypal_ext/LinkedSessionCreate.html'
    success_url = reverse_lazy('linked_sessions_list')

    def form_valid(self, form):
        #       we create here the corresponding PPP objects
        cur_linked_session = form.save()
        session = form.instance.session
        for p in session.get_participants():
            ppp = p.payouts.create(linked_session=cur_linked_session,
                                   amount=p.payoff_plus_participation_fee(),
                                   email=random.choice(debug_emails)
                                   )
        # form.instance.created_by = self.request.user
        return super().form_valid(form)


# to delete linked session
class DeleteLinkedSessionView(vanilla.DeleteView):
    model = models.LinkedSession
    template_name = 'paypal_ext/LinkedSessionDelete.html'
    success_url = reverse_lazy('linked_sessions_list')


# view to show linked session
class ListLinkedSessionsView(vanilla.ListView):
    template_name = 'paypal_ext/LinkedSessionList.html'
    url_name = 'linked_sessions_list'
    url_pattern = r'^linked_sessions/$'
    display_name = 'Linked sessions management for Paypal payments'
    model = models.LinkedSession


# what is shown to the participants who start the study (to collect their emails for future payments).
class EntryPointView(vanilla.View):
    ...


# to show list of processed batches.
class ListBatchesView(vanilla.ListView):
    ...


# to process payments (based on PPP model). inline formset
#  based on Linked Session as parent object, and PPPs as children
class DisplayLinkedSessionView(FormView):
    template_name = 'paypal_ext/LinkedSession.html'
    form_class = forms.EmptyForm

    def get_success_url(self):
        if self.successful_batch:
            return reverse('batch_detail', kwargs={'pk': self.successful_batch})
        else:
            return reverse_lazy('linked_sessions_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        linked_session = models.LinkedSession.objects.get(pk=self.kwargs['pk'])
        q = linked_session.payouts.filter(transaction_status='NOT PAID').exclude(
            Q(email__isnull=True) | Q(email__exact='') | Q(amount__isnull=True))
        processed_ppps = linked_session.payouts.exclude(transaction_status='NOT PAID')
        context.update({'linked_session': linked_session,
                        'ppp_formset': PPPFormSet(self.request.POST or None,
                                                  instance=linked_session,
                                                  queryset=q),
                        'processed_payments': processed_ppps,
                        'to_process_payments': q,
                        })
        return context

    def form_invalid(self, form):
        return super().form_invalid(form)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            context = self.get_context_data()
            linked_session = context['linked_session']
            ppps = context['ppp_formset']
            with transaction.atomic():
                if ppps.is_valid():
                    objs = ppps.save(commit=False)
                    num_payments = sum([ppp.to_pay for ppp in objs])
                    if num_payments > 0:
                        batch = Batch.objects.create(email_subject=conf.default_email_subject,
                                                     email_message=conf.default_email_message,
                                                     sender_batch_id=generate_random_string(),
                                                     linked_session=linked_session)
                        for o in objs:
                            o.payout_item_id = generate_random_string()
                            o.batch = batch

                        items = [o.get_payout_item() for o in objs]
                        batch.batch_body = batch.get_payout_body_of_batch(items)
                        batch.save()
                        processed_batch = paypal.create(batch)
                        # if there are any errors on paypal execution
                        if processed_batch['status'] == 'Failed':
                            # we store info about failed batches JIC
                            paypal_error = processed_batch['error']
                            FailedBatch.objects.create(error_message=paypal_error,
                                                       error_level=processed_batch['error_level'])
                            form.add_error(field=None, error=paypal_error)
                            batch.delete()
                            return self.form_invalid(form)
                        # TODO: later on perhaps change pk to payout_batch_id
                        self.successful_batch = batch.pk
                    else:
                        # if somebody submits the form without any payments
                        # unlikely to happen but JIC
                        self.successful_batch = None
                    ppps.save()
                else:
                    # if there are any errors in formset:
                    return self.form_invalid(form)
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class PPPUpdateView(vanilla.UpdateView):
    template_name = 'paypal_ext/EditPPP.html'
    url_name = 'edit_ppp'
    url_pattern = r'^ppp/(?P<pk>[a-zA-Z0-9_-]+)/$'
    model = models.PayPalPayout
    fields = ['email', 'amount']

    def get_success_url(self):
        return reverse('list_ppp_records', kwargs={'pk': self.object.linked_session.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['success_url'] = self.get_success_url()
        return context


class BatchListView(ListView):
    template_name = 'paypal_ext/BatchList.html'
    url_name = 'batches'
    url_pattern = r'^linked_session/(?P<pk>[a-zA-Z0-9_-]+)/batches/$'
    model = models.Batch

    def get_queryset(self):
        objs = Batch.objects.filter(linked_session__pk=self.kwargs['pk'])
        return objs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        batches = self.get_queryset()
        infoall = []
        for b in batches:
            if b.batch_status not in BATCH_IGNORED_STATUSES:
                infoall.append(paypal.get(b, header_only=True))
        context['infoall'] = infoall
        return context


class BatchDetailView(DetailView):
    template_name = 'paypal_ext/ViewBatch.html'
    url_name = 'batch_detail'
    url_pattern = r'^batch/(?P<pk>[a-zA-Z0-9_-]+)/$'
    model = models.Batch

    def get_context_data(self, **kwargs):
        batch = self.get_object()
        context = super().get_context_data(**kwargs)
        ppps = self.object.payouts.all()
        if batch.batch_status not in BATCH_IGNORED_STATUSES:
            updated_batch_info = paypal.get(batch)
            batch.update_status(updated_batch_info)
        context.update({'ppps': ppps,
                        'batch_info': batch.info})
        return context


# * Ajax view to update the status of batches
class AjaxUpdateBatchView(vanilla.UpdateView):
    ...


# * Ajax view to update the status of payments
class AjaxUpdatePPPView(vanilla.UpdateView):
    ...
