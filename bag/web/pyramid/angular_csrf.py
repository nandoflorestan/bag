"""Make Pyramid 1.7+ play ball with AngularJS to achieve CSRF protection.

To use this module, include it in your application configuration::

    # Integrate with Angular for CSRF protection:
    config.include('bag.web.pyramid.angular_csrf')

For any GET requests, this causes the response to have a
cookie containing the CSRF token, just as Angular 1.x wants it.

In subsequent AJAX requests (with verbs different than GET),
Angular will send the token back in a header 'X-XSRF-Token'.

Pyramid will validate the CSRF token before calling your view handler.

Relevant angular documentation is at
https://docs.angularjs.org/api/ng/service/$http

Relevant Pyramid documentation is at
http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/sessions.html#checking-csrf-tokens-automatically
"""

from pyramid.events import NewResponse

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
        # print(ev.request.session.session_id, token)
        if ev.request.cookies.get('XSRF-TOKEN') != token:
            ev.response.set_cookie(COOKIE_NAME, token, overwrite=True)


def includeme(config):
    """Set up the angular_csrf protection scheme for a Pyramid application."""
    config.add_subscriber(on_GET_request_setup_csrf_cookie, NewResponse)
    config.set_default_csrf_options(require_csrf=True, header=HEADER_NAME)
