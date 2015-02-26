# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from nine import nine


@nine
class Problem(Exception):
    '''Service (or "action") layers should be independent of web frameworks;
        however, often I feel I want the service layer to determine the
        HTTP code returned by a web service, instead of the controller layer.
        So I raise this exception in the service layer and capture it in the
        controller layer.

        Very useful when coupled with the
        `ajax_view decorator <https://github.com/nandoflorestan/bag/blob/master/bag/web/pyramid/views.py>`_, which does the capture part.

        When developing a user interface of any kind, it is great when all the
        webservices respect a standardized interface for returning errors.
        This class uses these fields:

        - error_msg: the string to be displayed to the end user
        - error_type: a sort of title; usually the HTTP error title
        - error_debug: should NOT be shown to end users; for devs only
        '''

    HTTP = {  # http://en.wikipedia.org/wiki/List_of_HTTP_status_codes
        # TODO Complete this map with the remaining 4xx and 5xx
        # 4xx Client error
        400: 'Bad request',
        401: 'Unauthorized',
        403: 'Forbidden',
        404: 'Not found',
        409: 'Conflict',
        410: 'Gone',
        413: 'Request entity too large',
        422: 'Unprocessable entity',
        # 5xx Server error
        500: 'Internal server error',
        }

    def __init__(self, msg, http_code=500, error_type=None, error_debug=None, **kw):
        self.http_code = int(http_code)
        kw['error_type'] = error_type or self.HTTP[self.http_code]
        kw['error_msg'] = msg
        kw['error_debug'] = error_debug
        self.kw = kw

    def to_dict(self):
        return self.kw

    def __repr__(self):
        return '<{} {}>'.format(type(self).__name__, self.kw)

    def __str__(self):
        return self.kw['error_msg']


class Unprocessable(Exception):
    '''Exception that mimics Colander's Invalid, because both have an
        ``asdict()`` method. However, this one can be instantiated
        without a schema. Example usage::

            if not data.get('user_email'):
                raise Unprocessable(user_email='This field is required.')
        '''

    def __init__(self, **adict):
        self.adict = adict

    def asdict(self):
        return self.adict
