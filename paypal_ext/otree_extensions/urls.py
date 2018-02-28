from django.conf.urls import url, include
from paypal_ext import views as v
from django.conf import settings
from django.contrib.auth.decorators import login_required


urlpatterns = []
view_classes = [v.PPPUpdateView, v.BatchDetailView, v.BatchListView, v.PPPDetailView, v.DisplayLinkedSessionView,
                v.CreateLinkedSessionView, v.DeleteLinkedSessionView]

# to protect if auth level
for ViewCls in view_classes:
    if settings.AUTH_LEVEL in {'DEMO', 'STUDY'}:
        as_view = login_required(ViewCls.as_view())
    else:
        as_view = ViewCls.as_view()
    urlpatterns.append(url(ViewCls.url_pattern, as_view, name=ViewCls.url_name))
