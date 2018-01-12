# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http import JsonResponse

from .models import APIKey


class RequireAPIKeyMixin(object):
    '''A mixin to check that a valid API key in the X-Api-Key header'''

    def dispatch(self, request, *args, **kwargs):
        self.api_key = APIKey.objects.filter(
            key=request.META.get('HTTP_X_API_KEY', '')).first()
        if not self.api_key:
            return JsonResponse(
                {'error': 'You must supply a valid API key in the X-Api-Key header'},
                status=403,
                json_dumps_params={'indent': 4},
            )
        return super(RequireAPIKeyMixin, self).dispatch(request, *args, **kwargs)
