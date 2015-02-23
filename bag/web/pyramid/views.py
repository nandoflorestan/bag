# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from functools import wraps
from json import dumps
from bag.web.exceptions import Problem
from pyramid.httpexceptions import HTTPError


def get_json_or_raise(request, expect=None):
    '''If the incoming json cannot be decoded, this is a bad request,
        so raise 400 instead of 500.

        The json body, when decoded, may become one of a number of types
        (usually dict or list). You can validate the type by passing
        an ``expect`` argument. If the json decodes
        to the wrong type, also raise 400 instead of 500.
        '''
    try:
        payload = request.json_body
    except ValueError as e:
        raise Problem('The server could not decode the request!',
                      http_code=400, error_debug=str(e))
    if expect is not None and not isinstance(payload, expect):
        raise Problem(
            'The server found unexpected content in the decoded request!',
            http_code=400,
            error_debug='Expected {}, got {}'.format(expect, type(payload)),
            )
    return payload


def ajax_view(view_function):
    '''Decorator for AJAX views that grabs certain exceptions and turns them
        into an error JSON response that contains:

        - "error_msg": the string to be displayed to end users
        - "error_type": a sort of title of the error
        - possibly other variables, too

        The transaction is not committed because we **raise** HTTPError.
        '''
    @wraps(view_function)
    def wrapper(context, request):
        try:
            o = view_function(context, request)
            # If *o* is a model instance, convert it to a dict.
            return o.to_dict() if hasattr(o, 'to_dict') else o
            # return o if isinstance(o, (Response, dict)) else o.to_dict()
        except Problem as e:
            comment = 'Problem found in action layer'
            http_code = e.http_code
            error_dict = e.to_dict()
        except Exception as e:
            if hasattr(e, 'asdict') and callable(e.asdict):
                comment = 'Colander validation error'
                http_code = 422  # Unprocessable Entity
                error_dict = e.asdict()
                error_dict['error_type'] = 'Invalid'
            else:
                raise  # Let this view-raised exception pass through
        raise HTTPError(
            status_int=http_code,
            content_type='application/json',
            body=dumps(error_dict),
            detail=error_dict['error_msg'],  # could be shown to end users
            comment=comment,  # not displayed to end users
            )
    return wrapper
