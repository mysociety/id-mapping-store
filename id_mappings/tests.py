# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import re

from django.test import Client, TestCase

from id_mappings.models import EquivalenceClaim, Identifier, Scheme
from api_keys.models import APIKey

ISO_TIMESTAMP_RE = re.compile(r'^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d.\d{6}[+-]\d\d:\d\d)$')

class FixtureMixin(object):

    def setUp(self):
        super(FixtureMixin, self).setUp()
        self.area_scheme = Scheme.objects.create(name='uk-area_id')
        self.wd_district_scheme = Scheme.objects.create(name='wikidata-district-item')
        self.area_identifier = Identifier.objects.create(
            value='gss:S17000017',
            scheme=self.area_scheme)
        self.wd_identifier = Identifier.objects.create(
            value='Q1529479',
            scheme=self.wd_district_scheme)
        EquivalenceClaim.objects.create(
            identifier_a=self.area_identifier,
            identifier_b=self.wd_identifier)
        self.api_key = APIKey.objects.create(
            key='fb8f58725b644763230d4df3c74195b5',
            notes='Example API key for tests',
        )


class TestIdentiferLookup(FixtureMixin, TestCase):

    def test_identifier_not_found_via_scheme_name(self):
        c = Client()
        response = c.get('/identifier/uk-area_id/gss:MADEUP')
        assert response.status_code == 404

    def test_identifier_not_found_via_scheme_id(self):
        c = Client()
        path = '/identifier/{0}/gss:MADEUP'.format(self.area_scheme.id)
        response = c.get(path)
        assert response.status_code == 404

    def test_identifier_found_via_scheme_name(self):
        c = Client()
        response = c.get('/identifier/uk-area_id/gss:S17000017')
        assert response.status_code == 200
        returned_data = json.loads(response.content)
        assert returned_data['results'] == [
            {
                'scheme_id': self.wd_district_scheme.id,
                'scheme_name': 'wikidata-district-item',
                'value': 'Q1529479',
            }
        ]
        history = returned_data['history']
        assert len(history) == 1
        assert ISO_TIMESTAMP_RE.search(history[0]['created'])
        history[0].pop('created')
        assert history[0] == {
            'identifier': {
                'scheme_id': self.wd_district_scheme.id,
                'scheme_name': 'wikidata-district-item',
                'value': 'Q1529479',
            },
            'deprecated': False,
            'comment': '',
        }

    def test_identifier_found_via_scheme_id(self):
        c = Client()
        path = '/identifier/{0}/gss:S17000017'.format(self.area_scheme.id)
        response = c.get(path)
        assert response.status_code == 200
        returned_data = json.loads(response.content)
        assert returned_data['results'] == [
            {
                'scheme_id': self.wd_district_scheme.id,
                'scheme_name': 'wikidata-district-item',
                'value': 'Q1529479',
            }
        ]
        history = returned_data['history']
        assert len(history) == 1
        assert ISO_TIMESTAMP_RE.search(history[0]['created'])
        history[0].pop('created')
        assert history[0] == {
            'identifier': {
                'scheme_id': self.wd_district_scheme.id,
                'scheme_name': 'wikidata-district-item',
                'value': 'Q1529479',
            },
            'deprecated': False,
            'comment': '',
        }

    def test_identifier_includes_claim_comments(self):
        ec = EquivalenceClaim.objects.get()
        ec.comment = 'Created a mapping for Glasgow (SPE)'
        ec.save()
        c = Client()
        path = '/identifier/{0}/gss:S17000017'.format(self.area_scheme.id)
        response = c.get(path)
        assert response.status_code == 200
        returned_data = json.loads(response.content)
        assert returned_data['results'] == [
            {
                'scheme_id': self.wd_district_scheme.id,
                'scheme_name': 'wikidata-district-item',
                'value': 'Q1529479',
            }
        ]
        history = returned_data['history']
        assert len(history) == 1
        assert ISO_TIMESTAMP_RE.search(history[0]['created'])
        history[0].pop('created')
        assert history[0] == {
            'identifier': {
                'scheme_id': self.wd_district_scheme.id,
                'scheme_name': 'wikidata-district-item',
                'value': 'Q1529479',
            },
            'deprecated': False,
            'comment': 'Created a mapping for Glasgow (SPE)',
        }

    def test_no_identifier_returned_after_deprecation(self):
        # Create a new claim which is the same, but marked deprecated:
        deprecated_claim = EquivalenceClaim.objects.get()
        deprecated_claim.pk = None
        deprecated_claim.deprecated = True
        deprecated_claim.save()
        c = Client()
        path = '/identifier/{0}/gss:S17000017'.format(self.area_scheme.id)
        response = c.get(path)
        assert response.status_code == 200
        returned_data = json.loads(response.content)
        assert returned_data['results'] == []
        history = returned_data['history']
        assert len(history) == 2
        for history_item in history:
            assert ISO_TIMESTAMP_RE.search(history_item['created'])
            history_item.pop('created')
        assert history[0] == {
            'identifier': {
                'scheme_id': self.wd_district_scheme.id,
                'scheme_name': 'wikidata-district-item',
                'value': 'Q1529479',
            },
            'deprecated': False,
            'comment': '',
        }
        assert history[1] == {
            'identifier': {
                'scheme_id': self.wd_district_scheme.id,
                'scheme_name': 'wikidata-district-item',
                'value': 'Q1529479',
            },
            'deprecated': True,
            'comment': '',
        }


class TestCreateEquivalence(FixtureMixin, TestCase):

    def test_create_equivalence_with_no_api_token_fails(self):
        c = Client()
        path = '/equivalence-claim'
        response = c.post(
            path,
            json.dumps({
                'identifier_a': {
                    'scheme_id': self.area_scheme.id,
                    'value': 'gss:S14000003',
                },
                'identifier_b': {
                    'scheme_id': self.wd_district_scheme.id,
                    'value': 'Q408547',
                }
            }),
            content_type='application/json'
        )
        assert response.status_code == 403

    def test_create_equivalence_new_identifiers(self):
        c = Client()
        path = '/equivalence-claim'
        response = c.post(
            path,
            json.dumps({
                'identifier_a': {
                    'scheme_id': self.area_scheme.id,
                    'value': 'gss:S14000003',
                },
                'identifier_b': {
                    'scheme_id': self.wd_district_scheme.id,
                    'value': 'Q408547',
                }
            }),
            content_type='application/json',
            HTTP_X_API_KEY=self.api_key.key,
        )
        assert response.status_code == 201
        # Now those two new identifiers should exist:
        area_identifier = Identifier.objects.get(
            scheme=self.area_scheme,
            value='gss:S14000003')
        wd_identifier = Identifier.objects.get(
            scheme=self.wd_district_scheme,
            value='Q408547')
        EquivalenceClaim.objects.get(
            identifier_a=area_identifier,
            identifier_b=wd_identifier,
            deprecated=False,
        )

    def test_create_equivalence_identifiers_exist(self):
        c = Client()
        path = '/equivalence-claim'
        response = c.post(
            path,
            json.dumps({
                'identifier_a': {
                    'scheme_id': self.area_scheme.id,
                    'value': self.area_identifier.value,
                },
                'identifier_b': {
                    'scheme_id': self.wd_district_scheme.id,
                    'value': self.wd_identifier.value,
                }
            }),
            content_type='application/json',
            HTTP_X_API_KEY=self.api_key.key,
        )
        assert response.status_code == 201
        # There should be no new identifiers created, just those from
        # the fixture mixin.
        assert 1 == Identifier.objects.filter(scheme=self.area_scheme).count()
        assert 1 == Identifier.objects.filter(scheme=self.wd_district_scheme).count()
        # However, it should create a new equivalence claim, so there
        # should be two now:
        assert 2 == EquivalenceClaim.objects.filter(
            identifier_a=self.area_identifier,
            identifier_b=self.wd_identifier,
            deprecated=False).count()
        parsed_response = json.loads(response.content)
        assert not parsed_response['identifier_a']['created']
        assert not parsed_response['identifier_b']['created']

    def test_create_equivalence_claim_with_comment(self):
        c = Client()
        path = '/equivalence-claim'
        response = c.post(
            path,
            json.dumps({
                'identifier_a': {
                    'scheme_id': self.area_scheme.id,
                    'value': self.area_identifier.value,
                },
                'identifier_b': {
                    'scheme_id': self.wd_district_scheme.id,
                    'value': self.wd_identifier.value,
                },
                'comment': 'UK: mapping from ONS ID to Wikidata item ID for Glasgow (Scottish Parliament region)'
            }),
            content_type='application/json',
            HTTP_X_API_KEY=self.api_key.key,
        )
        assert response.status_code == 201
        # There should be no new identifiers created, just those from
        # the fixture mixin.
        assert 1 == Identifier.objects.filter(scheme=self.area_scheme).count()
        assert 1 == Identifier.objects.filter(scheme=self.wd_district_scheme).count()
        # However,
        claims_after = EquivalenceClaim.objects.filter(
            identifier_a=self.area_identifier,
            identifier_b=self.wd_identifier,
            deprecated=False).order_by('created')
        assert 2 == claims_after.count()
        assert claims_after.last().comment == 'UK: mapping from ONS ID to Wikidata item ID for Glasgow (Scottish Parliament region)'

    def test_create_deprecation(self):
        c = Client()
        path = '/equivalence-claim'
        response = c.post(
            path,
            json.dumps({
                'identifier_a': {
                    'scheme_id': self.area_scheme.id,
                    'value': self.area_identifier.value,
                },
                'identifier_b': {
                    'scheme_id': self.wd_district_scheme.id,
                    'value': self.wd_identifier.value,
                },
                'deprecated': True,
            }),
            content_type='application/json',
            HTTP_X_API_KEY=self.api_key.key,
        )
        assert response.status_code == 201
        # There should be no new identifiers created, just those from
        # the fixture mixin.
        assert 1 == Identifier.objects.filter(scheme=self.area_scheme).count()
        assert 1 == Identifier.objects.filter(scheme=self.wd_district_scheme).count()
        # However, it should create a new equivalence claim
        # contradicting the existing one:
        assert 1 == EquivalenceClaim.objects.filter(
            identifier_a=self.area_identifier,
            identifier_b=self.wd_identifier,
            deprecated=True).count()


class TestSchemeList(FixtureMixin, TestCase):

    def test_all_schemes_returned(self):
        c = Client()
        path = '/scheme'
        response = c.get(path)
        assert response.status_code == 200
        parsed_response = json.loads(response.content)
        assert parsed_response == {
            'results': [
                {
                    'id': self.area_scheme.id,
                    'name': self.area_scheme.name,
                },
                {
                    'id': self.wd_district_scheme.id,
                    'name': self.wd_district_scheme.name,
                },
            ]
        }

class TestListIdentifiersForScheme(FixtureMixin, TestCase):

    def test_no_identifiers_for_new_scheme(self):
        unused_scheme = Scheme.objects.create(name='unused')
        c = Client()
        path = '/scheme/{0}'.format(unused_scheme.pk)
        response = c.get(path)
        assert response.status_code == 200
        parsed_response = json.loads(response.content)
        assert parsed_response == {'results': {}}

    def test_scheme_used_in_identifier_a(self):
        c = Client()
        path = '/scheme/{0}'.format(self.area_scheme.pk)
        response = c.get(path)
        assert response.status_code == 200
        parsed_response = json.loads(response.content)
        assert parsed_response == {
            'results': {
                'gss:S17000017': [
                    {
                        'value': 'Q1529479',
                        'scheme_id': self.wd_district_scheme.id,
                        'scheme_name': self.wd_district_scheme.name,
                    }
                ]
            }
        }

    def test_scheme_used_in_identifier_b(self):
        c = Client()
        path = '/scheme/{0}'.format(self.wd_district_scheme.pk)
        response = c.get(path)
        assert response.status_code == 200
        parsed_response = json.loads(response.content)
        assert parsed_response == {
            'results': {
                'Q1529479': [
                    {
                        'value': 'gss:S17000017',
                        'scheme_id': self.area_scheme.id,
                        'scheme_name': self.area_scheme.name,
                    }
                ]
            }
        }

    def test_deprecated_equivalence_suppressed_from_scheme_a(self):
        deprecated_claim = EquivalenceClaim.objects.get()
        deprecated_claim.pk = None
        deprecated_claim.deprecated = True
        deprecated_claim.save()
        c = Client()
        path = '/scheme/{0}'.format(self.wd_district_scheme.pk)
        response = c.get(path)
        assert response.status_code == 200
        parsed_response = json.loads(response.content)
        assert parsed_response == {'results': {'Q1529479': []}}

    def test_deprecated_equivalence_suppressed_from_scheme_b(self):
        deprecated_claim = EquivalenceClaim.objects.get()
        deprecated_claim.pk = None
        deprecated_claim.deprecated = True
        deprecated_claim.save()
        c = Client()
        path = '/scheme/{0}'.format(self.area_scheme.pk)
        response = c.get(path)
        assert response.status_code == 200
        parsed_response = json.loads(response.content)
        assert parsed_response == {'results': {'gss:S17000017': []}}

    def test_multiple_identifiers_either_side_from_scheme_returned(self):
        gss_id = Identifier.objects.create(
            value='gss:S14000003', scheme=self.area_scheme)
        wd_id = Identifier.objects.create(
            value='Q408547', scheme=self.wd_district_scheme)
        EquivalenceClaim.objects.create(
            identifier_a=wd_id,
            identifier_b=gss_id,
        )
        # Now try to fetch all IDs from the Wikidata scheme:
        c = Client()
        path = '/scheme/{0}'.format(self.wd_district_scheme.pk)
        # There should be two queries here: one to fetch the scheme
        # from the URL and one to fetch the EquivalentClaim and all
        # dependent objects.
        with self.assertNumQueries(2):
            response = c.get(path)
        assert response.status_code == 200
        parsed_response = json.loads(response.content)
        results = parsed_response['results']
        assert len(results) == 2
        # Sort the results for a predictable comparison:
        assert sorted(results.items()) == [
            ('Q1529479',
             [{'scheme_id': 29,
               'scheme_name': 'uk-area_id',
               'value': 'gss:S17000017'}]),
            ('Q408547',
             [{'scheme_id': 29,
               'scheme_name': 'uk-area_id',
               'value': 'gss:S14000003'}])
        ]
