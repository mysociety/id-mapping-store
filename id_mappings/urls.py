from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r'^identifier/(?P<scheme>.+?)/(?P<value>.*)$',
        views.IdentifierLookupView.as_view(),
        name='identifier-lookup'),
]
