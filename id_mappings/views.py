# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import re

from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils.functional import cached_property
from django.views.generic import View, DetailView, ListView

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
        return JsonResponse(context['data'], json_dumps_params={'indent': 4})


@method_decorator(csrf_exempt, name='dispatch')
class EquivalenceClaimCreateView(View):

    http_method_names = 'post'

    def post(self, request, *args, **kwargs):
        posted_data = json.loads(request.body)
        deprecated = posted_data.get('deprecated', False)
        id_data_a = posted_data['identifier_a']
        id_data_b = posted_data['identifier_b']
        scheme_a_id = id_data_a['scheme_id']
        scheme_b_id = id_data_b['scheme_id']
        scheme_a = get_object_or_404(Scheme, pk=scheme_a_id)
        scheme_b = get_object_or_404(Scheme, pk=scheme_b_id)
        a, created_a = Identifier.objects.get_or_create(
            scheme=scheme_a, value=id_data_a['value'])
        b, created_b = Identifier.objects.get_or_create(
            scheme=scheme_b, value=id_data_b['value'])
        EquivalenceClaim.objects.create(
            identifier_a=a, identifier_b=b, deprecated=deprecated
        )
        return JsonResponse(
            {
                'identifier_a': {
                    'created': created_a
                },
                'identifier_b': {
                    'created': created_b
                },
            },
            status=201,
            json_dumps_params={'indent': 4},
        )


class SchemeListView(ListView):

    queryset = Scheme.objects.order_by('id')

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(
            {
                'results': [
                    {
                        'id': scheme.id,
                        'name': scheme.name,
                    }
                    for scheme in context['object_list']
                ]
            },
            json_dumps_params={'indent': 4},
        )
