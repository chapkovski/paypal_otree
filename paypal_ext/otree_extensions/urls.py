from django.conf.urls import url, include
from paypal_ext import views as v

urlpatterns = [url(r'^linkedsession/(?P<pk>[a-zA-Z0-9_-]+)/delete/$', v.DeleteLinkedSessionView.as_view(),
                   name='delete_linked_session'),
               url(r'^linkedsession/create/$', v.CreateLinkedSessionView.as_view(),
                   name='create_linked_session'),
               ]
