# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from functools import wraps
from json import dumps
from nine import basestring
from bag.web.exceptions import Problem
from pyramid.httpexceptions import HTTPError
from pyramid.response import Response


def get_json_or_raise(request, expect=None, dict_has=None):
    '''If the incoming json cannot be decoded, this is a bad request,
        so raise 400 instead of 500.

        Usage examples::

            get_json_or_raise(request)
            get_json_or_raise(request, expect=list)
            get_json_or_raise(request, dict_has=[('email', str), ('age', int)])
            get_json_or_raise(request, dict_has=[('amount', (int, float))])

        The json body, when decoded, may become one of a number of types
        (usually dict or list). You can validate the type by passing
        an ``expect`` argument. If the json decodes
        to the wrong type, also raise 400 instead of 500.

        You may also ensure that a decoded dictionary contains some
        required keys by passing as the ``dict_has`` argument a sequence of
        2-tuples where each elemaint contains 1) the required key names and
        2) the accepted value type(s). 400 is raised if a key is missing.
        '''
    try:
        payload = request.json_body
    except ValueError as e:
        raise Problem('The server could not decode the request as JSON!',
                      http_code=400, error_debug=str(e))
    if expect is not None and not isinstance(payload, expect):
        raise Problem(
            'The server found unexpected content in the decoded request!',
            http_code=400,
            error_debug='Expected {}, got {}'.format(
                expect, type(payload).__name__))
    if dict_has:
        if not isinstance(payload, dict):
            raise Problem(
                'The JSON request decodes to a {} instead of a dictionary.'
                .format(type(payload).__name__),
                http_code=400,
                error_debug=payload)
        for key, typ in dict_has:
            if key not in payload:
                raise Problem('The request must contain a "{}" variable.'
                              .format(key),  http_code=400)
            if not isinstance(payload[key], typ):
                raise Problem(
                    'The value of the "{}" variable is of type {}, but '
                    'should be {}.'.format(
                        key,  type(payload[key]).__name__,  typ.__name__),
                    http_code=400)
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
            detail=error_dict.get('error_msg'),  # could be shown to end users
            comment=comment,  # not displayed to end users
            )
    return wrapper


def xeditable_view(view_function):
    '''Decorator for AJAX views that need to be friendly towards x-editable,
        the famous edit-in-place component for AngularJS. x-editable likes
        us to return either an error string or "204 No content".
        '''
    @wraps(view_function)
    def wrapper(context, request):
        try:
            o = view_function(context, request)
        except Problem as e:
            comment = 'Problem found in action layer'
            http_code = e.http_code
            error_msg = e.to_dict().get('error_msg')
        except Exception as e:
            if hasattr(e, 'asdict') and callable(e.asdict):
                comment = 'Colander validation error'
                http_code = 422  # Unprocessable Entity
                error_msg = e.asdict().get('error_msg')
            else:
                raise  # Let this view-raised exception pass through
        else:
            if o is None:
                return Response(status_int=204)  # No content
            elif isinstance(o, basestring):
                comment = 'View returned error msg as a string'
                http_code = 400
                error_msg = o
            else:
                return o
        raise HTTPError(
            status_int=http_code, content_type='text/plain', body=error_msg,
            detail=error_msg,  # could be shown to end users
            comment=comment,  # not displayed to end users
            )
    return wrapper
