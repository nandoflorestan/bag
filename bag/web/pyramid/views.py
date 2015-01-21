# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from pyramid.httpexceptions import HTTPBadRequest


def get_json_or_raise(request, expect=None):
    '''If the json cannot be decoded, this is a bad request, so raise 400
        instead of 500.

        The decoded json may be of a number of types. You can validate the
        type, passing an ``expect`` argument. If the json decodes
        to the wrong type, also raise 400 instead of 500.
        '''
    try:
        payload = request.json_body
    except ValueError as e:
        raise HTTPBadRequest(detail=str(e))
    if expect is not None and not isinstance(payload, expect):
        raise HTTPBadRequest(
            detail='Expected {}, got {}'.format(expect, type(payload)))
    return payload
