# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils import timezone


class Scheme(models.Model):
    name = models.CharField(max_length=512)


class Identifier(models.Model):
    value = models.CharField(max_length=512)
    scheme = models.ForeignKey(Scheme)


class EquivalenceClaim(models.Model):
    identifier_a = models.ForeignKey(Identifier, related_name='claims_via_a')
    identifier_b = models.ForeignKey(Identifier, related_name='claims_via_b')
    created = models.DateTimeField(default=timezone.now)
    deprecated = models.BooleanField(default=False)
