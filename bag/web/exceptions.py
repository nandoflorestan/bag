"""Exceptions for web development."""


class Problem(Exception):
    """Great exception class for application-level errors.

    Service (or "action") layers should be independent of web frameworks;
    however, often I feel I want the service layer to determine the
    HTTP code returned by a web service, instead of the controller layer.
    So I raise this exception in the service layer and capture it in the
    controller layer.

    Very useful when coupled with the
    `ajax_view decorator <https://github.com/nandoflorestan/bag/blob/master/bag/web/pyramid/views.py>`_, which does the capture part.

    When developing a user interface of any kind, it is great when all the
    webservices respect a standardized interface for returning errors.
    This class outputs these fields by convention:

    - error_msg: the string to be displayed to the end user
    - error_title: by default the HTTP error title
    - error_debug: should NOT be shown to end users; for devs only
    """

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

    def __init__(self, error_msg, status_int=400, error_title=None,
                 error_debug=None, **kw):
        self.status_int = int(status_int)
        assert str(self.status_int)[0] in ('4', '5')

        kw['error_title'] = error_title or self.HTTP[self.status_int]
        kw['error_msg'] = error_msg
        kw['error_debug'] = error_debug
        self.kw = kw

    def to_dict(self):
        return self.kw

    @property
    def error_msg(self):
        return self.kw['error_msg']

    @property
    def error_title(self):
        return self.kw['error_title']

    @property
    def error_debug(self):
        return self.kw['error_debug']

    def __repr__(self):
        return '<{} {}>'.format(type(self).__name__, self.error_msg)

    def __str__(self):
        return self.error_msg


def ensure(condition, *a, **kw):
    """Use an assert-like syntax to raise Problem exceptions."""
    if not condition:
        raise Problem(*a, **kw)


class Unprocessable(Exception):
    """Exception that mimics Colander's Invalid.

    ...because both have an ``asdict()`` method. However, this one can be
    instantiated without a schema. Example usage::

        if not data.get('user_email'):
            raise Unprocessable(user_email='This field is required.')
    """

    def __init__(self, **adict):
        self.adict = adict

    def asdict(self):
        return self.adict
