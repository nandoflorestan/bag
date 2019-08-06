"""Help for Pyramid view development."""

from functools import wraps
from json import dumps
from typing import Any, Callable

from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPError
from pyramid.response import Response

from bag import first
from bag.web.exceptions import Problem

try:
    from bag.web.pyramid import _
except ImportError:
    _ = str  # and i18n is disabled.

ViewHandler = Callable[[Any, Any], Any]  # context, request, return value


def get_json_or_raise(request, expect=None, dict_has=None):
    """Obtain and validate incoming JSON, raising Problem if necessary.

    If the incoming json cannot be decoded, this is a bad request,
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
    """
    try:
        payload = request.json_body
    except ValueError as e:
        raise Problem('The server could not decode the request as JSON!',
                      error_debug=str(e))
    if expect is not None and not isinstance(payload, expect):
        raise Problem(
            'The server found unexpected content in the decoded request!',
            error_debug='Expected {}, got {}'.format(
                expect, type(payload).__name__))
    if dict_has:
        if not isinstance(payload, dict):
            raise Problem(
                'The JSON request decodes to a {} instead of a dictionary.'
                .format(type(payload).__name__),
                error_debug=payload)
        for key, typ in dict_has:
            if key not in payload:
                raise Problem('The request must contain a "{}" variable.'
                              .format(key))
            if not isinstance(payload[key], typ):
                raise Problem(
                    'The value of the "{}" variable is of type {}, but '
                    'should be {}.'.format(
                        key, type(payload[key]).__name__, typ.__name__))
    return payload


def ajax_view(view_function: ViewHandler) -> ViewHandler:
    """Decorate AJAX views to...

    - treat certain exceptions
    - convert the result to a dictionary if necessary.

    This decorator grabs certain exceptions and turns them
    into an error JSON response that contains:

    - "error_msg": the string to be displayed to end users
    - "error_title": the string to be displayed as a header
    - "validation": a dictionary of validation errors where keys are
      field names and values are the respective errors
    - possibly other variables, too

    The transaction is not committed because we **raise** HTTPError.
    """
    @wraps(view_function)
    def wrapper(context, request):
        try:
            val = view_function(context, request)
        except Problem as e:
            adict = e.to_dict()
            raise HTTPError(
                status_int=e.status_int,
                content_type='application/json',
                charset='utf-8',
                body=dumps(adict),
                detail=e.error_msg,  # could be shown to end users
                comment=e.error_debug,  # not displayed to end users
            )
        except Exception as e:
            maybe_raise_unprocessable(e)
            raise  # or let this view-raised exception pass through
        else:
            if val is None:
                raise RuntimeError("Error: None returned by {}()".format(
                    view_function.__qualname__))
            # If *val* is a model instance, convert it to a dict.
            return val.to_dict() if hasattr(val, 'to_dict') else val
    return wrapper


def maybe_raise_unprocessable(exc: Exception, **adict) -> None:
    """Raise if the provided exception looks like a validation error.

    Raise 422 Unprocessable Entity, optionally with additional information.
    """
    if hasattr(exc, 'asdict') and callable(exc.asdict):  # type: ignore
        error_msg = getattr(
            exc, 'error_msg', _('Please correct error(s) in the form.'))
        adict['invalid'] = exc.asdict()  # type: ignore
        adict.setdefault('error_title', 'Invalid')
        adict.setdefault('error_msg', error_msg)
        raise HTTPError(
            status_int=422,  # Unprocessable Entity
            content_type='application/json',
            charset='utf-8',
            body=dumps(adict),
            detail=error_msg,  # could be shown to end users
            # *comment* is not displayed to end users:
            comment=str(exc) or 'Form validation error',
        )


def xeditable_view(view_function: ViewHandler) -> ViewHandler:
    """Decorate AJAX views that need to be friendly towards x-editable.

    x-editable is a famous edit-in-place component for AngularJS.
    x-editable likes text/plain instead of JSON responses; so it likes
    us to return either an error string or "204 No content".
    """
    @wraps(view_function)
    def wrapper(context, request):
        try:
            val = view_function(context, request)
        except Problem as e:
            comment = 'Problem found in action layer'
            status_int = e.status_int
            error_msg = e.error_msg
        except Exception as e:
            if hasattr(e, 'asdict') and callable(e.asdict):
                comment = 'Form validation error'
                status_int = 422  # Unprocessable Entity
                error_msg = first(e.asdict().values())
            else:
                raise  # Let this view-raised exception pass through
        else:
            if val is None:
                return Response(status_int=204)  # No content
            elif isinstance(val, str):
                comment = 'View returned error msg as a string'
                status_int = 400
                error_msg = val
            else:
                return val
        raise HTTPError(
            status_int=status_int,
            content_type='text/plain',
            charset='utf-8',
            body=error_msg,
            detail=error_msg,  # could be shown to end users
            comment=comment,  # not displayed to end users
        )
    return wrapper


def serve_preloaded(
    config: Configurator, route_name: str, route_path: str, payload: str,
    encoding: str = '', content_type: str = '',
) -> None:
    """Read a file (such as robots.txt or favicon.ini) into memory.

    ...then set up a view that serves it.

    Pass no ``encoding`` if the file is binary.  If text, pass the encoding
    in which the file should be read (usually 'utf-8').

    Usage::

        from bag.web.pyramid.views import serve_preloaded
        serve_preloaded(
            config,
            route_name='robots',
            route_path='robots.txt',
            payload='my_package:static/robots.txt',
            encoding='utf-8')
        serve_preloaded(
            config,
            route_name='favicon',
            route_path='favicon.ico',
            payload='my_package:static/favicon.ico',
            content_type='image/x-icon',
        )
    """
    from os.path import getmtime, getsize
    from pyramid.resource import abspath_from_resource_spec
    from pyramid.response import Response

    path = abspath_from_resource_spec(payload)

    if not content_type:
        from mimetypes import guess_type
        content_type = guess_type(path)[0] or 'application/octet-stream'

    if encoding:
        stream = open(path, 'r', encoding=encoding)
    else:
        stream = open(path, 'rb')  # type: ignore

    kwargs = dict(
        content_type=content_type,
        body=stream.read(),
        last_modified=getmtime(path),
        content_length=getsize(path),
    )
    stream.close()

    def preloaded_view(request):  # This closure is the view handler
        return Response(**kwargs)

    config.add_route(route_name, route_path)
    config.add_view(preloaded_view, route_name=route_name)
