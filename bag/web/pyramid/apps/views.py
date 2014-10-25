# -*- coding: utf-8 -*-

'''Useful base views, functions and decorators for the view layer of
apps that use the Pyramid web framework.
'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from pyramid.decorator import reify
from pyramid.exceptions import Forbidden
from pyramid.i18n import get_localizer
from pyramid.renderers import get_renderer
from pyramid.settings import asbool
from pyramid.url import route_url
from nine import basestring, str
from ....text import uncommafy


class BaseView(object):
    '''Base class for views.'''

    def __init__(self, request):
        self.request = request

    @reify
    def tr(self):
        return get_localizer(self.request).translate

    def url(self, name, *a, **kw):
        '''A route_url that is easier to use.'''
        return route_url(name, self.request, *a, **kw)


undefined = object()


class BaseViewForDeform(BaseView):
    def model_to_dict(self, model, key_provider):
        '''Helps when using Deform.

        *key_provider* can be:

        * a comma-delimited string of key names,
        * a list of strings representing key names,
        * a colander.Schema (or subclass).

        Returns an appstruct dict with values taken from the model.
        '''
        import colander as c
        d = {}

        if isinstance(key_provider, basestring):
            key_provider = uncommafy(key_provider)
        elif not issubclass(key_provider, list):
            key_provider = [n.name for n in key_provider.__all_schema_nodes__]
        for k in key_provider:
            val = getattr(model, k, undefined)
            if val is undefined:
                continue
            d[k] = c.null if val is None else val
        return d

    def dict_to_model(self, adict, model):
        '''Helps when using Deform.'''
        import colander as c
        for key, val in adict.items():
            setattr(model, key, None if val is c.null else val)
        return model


class ChameleonBaseView(object):
    '''Base view mixin class for projects that use Chameleon with macros.'''
    macro_cache = {}  # Global cache for Chameleon template macros

    def macro(self, template, macro_name):
        '''Loads macros from any template.
        If settings['reload_templates'] is false, also memoizes the macros.
        '''
        if asbool(self.request.registry.settings.get('reload_templates')):
            return get_renderer(template).implementation().macros[macro_name]
        else:
            macro_path = template + '|' + macro_name
            macro = self.macro_cache.get(macro_path)
            if not macro:
                self.macro_cache[macro_path] = macro = \
                    get_renderer(template).implementation().macros[macro_name]
            return macro


def authenticated(func):
    '''Decorator that redirects to Pyramid's Forbidden view
    if the user is not authenticated.

    Depends on your request object possessing a *user* instance variable.
    This can easily be configured::

        # str('user') returns a bytestring under Python 2 and a
        # unicode string under Python 3, which is what we need:
        config.set_request_property(get_user, str('user'), reify=True)
        # Alternatively, use the *nine* library's ``native_str``:
        config.set_request_property(get_user, native_str('user'), reify=True)
    '''

    def wrapper(self, *a, **kw):
        if self.request.user:
            return func(self, *a, **kw)
        else:
            raise Forbidden()
    return wrapper


def get_request_class(User=None, sas=None, PageDeps=None):
    '''You can use this on Pyramid/SQLAlchemy apps.
    Returns a nice Request class which
    memoizes the user object (if the User class is passed in) and
    uses PageDeps if passed in.
    '''
    from pyramid.request import Request
    if User:
        from pyramid.security import authenticated_userid
        if not sas:
            from .models.user import sas

    class CustomRequest(Request):
        def __init__(self, *a, **kw):
            super(CustomRequest, self).__init__(*a, **kw)
            if PageDeps:
                self.page_deps = PageDeps()

        if User:
            @reify
            def user(self):
                '''Memoized user object. If we always use request.user to
                retrieve the authenticated user, the query will happen
                only once per request, which is good for performance.
                '''
                userid = authenticated_userid(self)
                return sas.query(User).get(userid) if userid else None
    return CustomRequest
