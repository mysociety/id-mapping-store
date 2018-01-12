# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.test import Client, TestCase

from id_mappings.models import EquivalenceClaim, Identifier, Scheme


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
        assert returned_data == {
            'results': [
                {
                    'scheme_id': self.wd_district_scheme.id,
                    'scheme_name': 'wikidata-district-item',
                    'value': 'Q1529479',
                }
            ]
        }

    def test_identifier_found_via_scheme_id(self):
        c = Client()
        path = '/identifier/{0}/gss:S17000017'.format(self.area_scheme.id)
        response = c.get(path)
        assert response.status_code == 200
        returned_data = json.loads(response.content)
        assert returned_data == {
            'results': [
                {
                    'scheme_id': self.wd_district_scheme.id,
                    'scheme_name': 'wikidata-district-item',
                    'value': 'Q1529479',
                }
            ]
        }


class TestCreateEquivalence(FixtureMixin, TestCase):

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
            content_type='application/json'
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
            content_type='application/json'
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
            content_type='application/json'
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
