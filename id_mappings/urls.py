from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r'^identifier/(?P<scheme>.+?)/(?P<value>.*)$',
        views.IdentifierLookupView.as_view(),
        name='identifier-lookup'),
    url(r'^equivalence-claim/?$',
        views.EquivalenceClaimCreateView.as_view(),
        name='equivalence-create'),
    url(r'^scheme/?$',
        views.SchemeListView.as_view(),
        name='scheme-list'),
]
