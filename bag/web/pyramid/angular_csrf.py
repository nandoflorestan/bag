# -*- coding: utf-8 -*-

"""Make Pyramid play ball with AngularJS to achieve CSRF protection.

To start using this module, include it in your application configuration::

    # Integrate with Angular for CSRF protection:
    config.include('bag.web.pyramid.angular_csrf')

For any GET requests, this causes the response to have a
cookie containing the CSRF token, just as Angular 1.3.x wants it.

In subsequent AJAX requests (with verbs different than GET),
Angular will send the token back in a header 'X-XSRF-Token'.

Now decorate your views with ``@csrf`` and they will raise HTTPForbidden when
the token is missing from the request. Usage::

    from bag.web.pyramid.angular_csrf import csrf

    @view_config(context=User, permission='edit_user',
                 accept='application/json', request_method='PUT',
                 renderer='json')
    @csrf
    def view_that_changes_a_user(context, request):
        ...

Although I haven't tested this, I hear one can also decorate a class::

    @view_defaults(decorator=csrf)
    class SomeView(object):
        ...

Relevant angular documentation is at
https://docs.angularjs.org/api/ng/service/$http
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from functools import wraps
from pyramid.events import NewResponse
from pyramid.httpexceptions import HTTPForbidden
from . import _

COOKIE_NAME = 'XSRF-TOKEN'
HEADER_NAME = 'X-XSRF-Token'  # different from Pyramid's default 'X-CSRF-Token'


def on_GET_request_setup_csrf_cookie(ev):
    """Set the XSRF-TOKEN cookie if necessary, on a GET request.

    If this is the first GET request, we set the CSRF token in a
    JavaScript readable session cookie called XSRF-TOKEN.
    Angular will pick it up for subsequent AJAX requests.
    """
    if ev.request.method == 'GET':  # and not 'static' in ev.request.path:
        token = ev.request.session.get_csrf_token()
        if ev.request.cookies.get('XSRF-TOKEN') != token:
            ev.response.set_cookie(COOKIE_NAME, token, overwrite=True)


def csrf(fn):
    """Decorator that protects a view handler against CSRF attacks."""
    @wraps(fn)
    def wrapper(context, request):
        token = request.headers.get(HEADER_NAME)
        session_token = request.session.get_csrf_token()
        # print(token, session_token)
        if token == session_token:
            return fn(context, request)
        else:
            raise HTTPForbidden(_(
                'Invalid CSRF token. Please try reloading the page.'))
    return wrapper


def includeme(config):
    """Set up the angular_csrf protection scheme for a Pyramid application."""
    config.add_subscriber(on_GET_request_setup_csrf_cookie, NewResponse)
