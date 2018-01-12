# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import EquivalenceClaim, Identifier, Scheme

admin.site.register(EquivalenceClaim)
admin.site.register(Identifier)
admin.site.register(Scheme)
