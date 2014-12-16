# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from pyramid.httpexceptions import HTTPBadRequest


def get_json_or_raise(request):
    '''If the json cannot be decoded, this is a bad request, so raise 400
        instead of 500.
        '''
    try:
        return request.json_body
    except ValueError as e:
        raise HTTPBadRequest(detail=str(e))
