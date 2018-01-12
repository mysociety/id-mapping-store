# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.validators import MinLengthValidator
from django.db import models


class APIKey(models.Model):
    key = models.CharField(
        max_length=128,
        validators=[MinLengthValidator(16)]
    )
    notes = models.CharField(max_length=256)
