# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils import timezone

from api_keys.models import APIKey


class Scheme(models.Model):
    name = models.CharField(max_length=512)

    def __repr__(self):
        return '{class_}(pk={pk}, name={name})'.format(
            class_=self.__class__.__name__,
            pk=self.pk,
            name=repr(self.name),
        )

    def __unicode__(self):
        return self.name


class Identifier(models.Model):
    value = models.CharField(max_length=512)
    scheme = models.ForeignKey(Scheme)

    def as_json(self):
        return {
            'value': self.value,
            'scheme_id': self.scheme.id,
            'scheme_name': self.scheme.name,
        }

    def __repr__(self):
        return '{class_}(value={value}, scheme={scheme})'.format(
            class_=self.__class__.__name__,
            value=repr(self.value),
            scheme=repr(self.scheme)
        )


class EquivalenceClaim(models.Model):
    identifier_a = models.ForeignKey(Identifier, related_name='claims_via_a')
    identifier_b = models.ForeignKey(Identifier, related_name='claims_via_b')
    created = models.DateTimeField(default=timezone.now)
    deprecated = models.BooleanField(default=False)
    api_key = models.ForeignKey(APIKey, blank=True, null=True)
    comment = models.TextField(default='')

    def other_identifier(self, not_this_identifier):
        if self.identifier_b == not_this_identifier:
            return self.identifier_a
        elif self.identifier_a == not_this_identifier:
            return self.identifier_b
        else:
            raise Exception('Neither identifier in {ec} was {i}'.format(
                ec=repr(self), i=not_this_identifier
            ))

    def __repr__(self):
        fmt = '{class_}<pk={pk} ({a_key}: {a_value}) <-> ({b_key}: {b_value}), created={created}{deprecated}>'
        return fmt.format(
            class_=self.__class__.__name__,
            pk=self.pk,
            a_key=self.identifier_a.scheme.name,
            b_key=self.identifier_b.scheme.name,
            a_value=self.identifier_a.value,
            b_value=self.identifier_b.value,
            created=self.created.isoformat(),
            deprecated=(' DEPRECATED' if self.deprecated else ''))
