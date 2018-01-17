# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import defaultdict, namedtuple, OrderedDict
import json
import re

from django.db.models import Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils.functional import cached_property
from django.views.generic import View, DetailView, ListView

from .models import EquivalenceClaim, Identifier, Scheme
from api_keys.views import RequireAPIKeyMixin


IdentifierFromClaim = namedtuple(
    'IdentifierFromClaim',
    ['identifier', 'deprecated', 'created', 'comment'])


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
    def equivalent_identifiers_from_claims(self):
        return [
            IdentifierFromClaim(
                identifier=ec.other_identifier(self.get_object()),
                deprecated=ec.deprecated,
                created=ec.created,
                comment=ec.comment,
            )
            for ec in EquivalenceClaim.objects.filter(
                Q(identifier_a=self.object) |
                Q(identifier_b=self.object)
            ).order_by('created')
        ]

    @cached_property
    def best_equivalent_identifiers(self):
        resolved = OrderedDict()
        for ifc in self.equivalent_identifiers_from_claims:
            resolved[ifc.identifier] = ifc.deprecated
        return [identifier for identifier, deprecated in resolved.items()
                if not deprecated]

    def get_context_data(self, **kwargs):
        context = super(IdentifierLookupView, self).get_context_data(**kwargs)
        context['data'] = {
            'results': [i.as_json() for i in self.best_equivalent_identifiers],
            'history': [
                {
                    'identifier': ifc.identifier.as_json(),
                    'created': ifc.created.isoformat(),
                    'deprecated': ifc.deprecated,
                    'comment': ifc.comment,
                }
                for ifc in self.equivalent_identifiers_from_claims
            ]
        }
        return context

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(context['data'], json_dumps_params={'indent': 4})


@method_decorator(csrf_exempt, name='dispatch')
class EquivalenceClaimCreateView(RequireAPIKeyMixin, View):

    http_method_names = 'post'

    def post(self, request, *args, **kwargs):
        posted_data = json.loads(request.body)
        deprecated = posted_data.get('deprecated', False)
        comment = posted_data.get('comment', '')
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
            identifier_a=a, identifier_b=b, deprecated=deprecated, comment=comment
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


class IdentifiersForSchemeView(View):

    def get(self, request, *args, **kwargs):
        scheme = get_object_or_404(Scheme, pk=kwargs['scheme'])
        identifier_to_resolved_identifiers = defaultdict(OrderedDict)
        # Find any claims with identifiers from that scheme, in order
        # of creation:
        for ec in EquivalenceClaim.objects.filter(
                Q(identifier_a__scheme=scheme) |
                Q(identifier_b__scheme=scheme)
            ).select_related('identifier_a__scheme', 'identifier_b__scheme').order_by('created'):
            # There might be an identifier with this scheme on either
            # or both sides of the equivalence claim, so try both:
            for identifier in (ec.identifier_a, ec.identifier_b):
                other_identifier = ec.other_identifier(identifier)
                if identifier.scheme == scheme:
                    other_ifc = IdentifierFromClaim(
                        identifier=other_identifier,
                        deprecated=ec.deprecated,
                        created=ec.created,
                        comment=ec.comment,
                    )
                    # The claims have been ordered by creation
                    # timestamp, so this wil leave us with the latest
                    # deprecation status:
                    identifier_to_resolved_identifiers[identifier.value][other_ifc.identifier] = other_ifc.deprecated
        # Filter out any deprecated relationships in the response:
        return JsonResponse(
            {
                'results': {
                    identifier:
                    [
                        other_scheme_identifier.as_json()
                        for other_scheme_identifier, deprecated
                        in mapped_identifiers.items() if not deprecated
                    ]
                    for identifier, mapped_identifiers
                    in identifier_to_resolved_identifiers.items()
                }
            }, json_dumps_params={'indent': 4}
        )
