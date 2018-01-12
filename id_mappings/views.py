# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from django.views.generic import DetailView

from .models import EquivalenceClaim, Identifier, Scheme

class IdentifierLookupView(DetailView):

    @cached_property
    def scheme_object(self):
        scheme_kwarg = self.kwargs['scheme']
        if re.search('^\d+$', scheme_kwarg):
            return Scheme.objects.get(pk=int(scheme_kwarg))
        else:
            return Scheme.objects.get(name=scheme_kwarg)

    def get_object(self):
        return get_object_or_404(
            Identifier, scheme=self.scheme_object, value=self.kwargs['value'])

    @cached_property
    def equivalent_identifiers(self):
        return [
            ec.identifier_a if ec.identifier_b == self.get_object() \
                else ec.identifier_b
            for ec in EquivalenceClaim.objects.filter(
                Q(identifier_a=self.object) |
                Q(identifier_b=self.object)
            ).order_by('created')
        ]

    def get_context_data(self, **kwargs):
        context = super(IdentifierLookupView, self).get_context_data(**kwargs)
        context['data'] = {
            'results': [
                {
                    'value': i.value,
                    'scheme_id': i.scheme.id,
                    'scheme_name': i.scheme.name,
                }
                for i in self.equivalent_identifiers
            ]
        }
        return context

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(context['data'])
