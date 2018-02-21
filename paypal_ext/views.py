from . import models
import vanilla
from django.core.urlresolvers import reverse_lazy
from .forms import SessionCreateForm
from django.views.generic.edit import CreateView

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


# what is shown to the participants who start the study (to collect their emails for future payments).
class EntryPointView(vanilla.View):
    ...


# to show list of processed batches.
class ListBatchesView(vanilla.ListView):
    ...

# to process payments (based on PPP model). inline formset based on Linked Session as parent object, and PPPs as children

class ProcessingPayoutsView(vanilla.View):
    ...


# * Ajax view to update the status of batches
class AjaxUpdateBatchView(vanilla.UpdateView):
    ...
# * Ajax view to update the status of payments
class AjaxUpdatePPPView(vanilla.UpdateView):
    ...