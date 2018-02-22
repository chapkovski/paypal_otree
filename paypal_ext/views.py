from . import models, forms
import vanilla
from django.core.urlresolvers import reverse_lazy
from .forms import SessionCreateForm, PPPFormSet
from django.views.generic.edit import CreateView
from .models import PayPalPayout as PPP
from django.db import transaction
import random
import string

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
                                   amount=p.payoff_plus_participation_fee())
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
class DisplayLinkedSessionView(vanilla.FormView):
    template_name = 'paypal_ext/LinkedSession.html'
    success_url = reverse_lazy('linked_sessions_list')
    form_class = forms.EmptyForm

    def get_context_data(self, **kwargs):
        linked_session = models.LinkedSession.objects.get(pk=self.kwargs['pk'])
        return {'linked_session': linked_session,
                'ppp_formset': PPPFormSet(self.request.POST or None, instance=linked_session),
                }

    def form_valid(self, form):
        context = self.get_context_data()
        ppps = context['ppp_formset']
        with transaction.atomic():
            if ppps.is_valid():
                # TODO: create a batch item if there are any changes and link them to updated objects
                # TODO: ccheck if PPP ojbects to work with, have emails, amounts, batches and payout_item_ids
                # TODO: submit a batch to payout in paypal, check for errors, return them if any

                objs = ppps.save(commit=False)
                for o in objs:
                    o.payout_item_id = ''.join(random.choice(string.ascii_lowercase) for i in range(12))
                ppps.save()

        return super().form_valid(form)


# * Ajax view to update the status of batches
class AjaxUpdateBatchView(vanilla.UpdateView):
    ...


# * Ajax view to update the status of payments
class AjaxUpdatePPPView(vanilla.UpdateView):
    ...
