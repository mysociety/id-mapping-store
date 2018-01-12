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
