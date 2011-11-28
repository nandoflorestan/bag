#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals  # unicode by default
import os
import stat
from pyramid.config import Configurator
from pyramid.decorator import reify


def isdir(s):
    """Return true if the pathname refers to an existing directory."""
    try:
        st = os.stat(s)
    except os.error:
        return False
    return stat.S_ISDIR(st.st_mode)


def makedirs(s):
    '''Make directories (if they don't exist already).'''
    if not isdir(s):
        os.makedirs(s)


class LocaleList(list):
    def add(self, id, name, title):
        self.append(dict(name=id, descr=name, title=title))


class PyramidStarter(object):
    '''Reusable configurator for nice Pyramid applications.'''

    def __init__ (self, name, appfile, settings, config, packages=[],
                  require_python27=False):
        '''Arguments:

        `name` is the name of your package;
        `appfile` should be, simply, __file__ (in other
        words, a string containing the path to the file that represents the
        Pyramid app).
        `settings` is the dictionary, provided by Pyramid, containing the
        configuration for the application as read from config files.
        `config` is the Pyramid configurator instance, or a dictionary that
        can be used to create such an instance.
        `packages` is a sequence of additional packages that should be
        scanned/enabled.
        '''
        if require_python27:
            self.require_python27()
        if not settings.has_key('app.name'):
            raise KeyError \
                ('Your configuration files are missing an "app.name" setting.')
        self.name = name
        self.packages = packages
        if isinstance(config, Configurator):
            self.config = config
        else:
            self.make_config(config, settings)
        self.directory = os.path.abspath(os.path.dirname(appfile))
        self.parent_directory = os.path.dirname(self.directory)
        from importlib import import_module
        self.module = import_module(self.name)
        # Create the _() function for internationalization
        from pyramid.i18n import TranslationStringFactory
        self._ = TranslationStringFactory(name)
        self._enable_locales()
        self.handlers = False  # which can be changed by enable_handlers()

    def _enable_locales(self):
        '''Gets a list of enabled locale names from settings, checks it
        against our known locales and stores in settings a list containing
        not only the locale names but also texts for links for changing the
        locale.
        '''
        # Get a list of enabled locale names from settings
        settings = self.settings
        locales_filter = settings.get('enabled_locales', 'en').split(' ')
        _ = self._
        # Check the settings against a list of supported locales
        locales = LocaleList()
        locales.add('en', _('English'), 'Change to English')
        locales.add('en_DEV', _('English-DEV'), 'Change to dev slang')
        locales.add('pt_BR', _('Brazilian Portuguese'), 'Mudar para português')
        locales.add('es', _('Spanish'), 'Cambiar a español')
        locales.add('de', _('German'), 'Auf Deutsch benutzen')
        # The above list must be updated when new languages are added
        enabled_locales = []
        for locale in locales_filter:
            for adict in locales:
                if locale == adict['name']:
                    enabled_locales.append(adict)
        # Replace the setting
        settings['enabled_locales'] = enabled_locales

    def make_config(self, adict, settings):
        """Creates *config*, a temporary wrapper of the registry.
        This method is intended to be overridden in subclasses.
        `adict` should contain request_factory, session_factory,
        authentication_policy, authorization_policy etc.
        """
        adict.setdefault('settings', settings)
        self.config = Configurator(**adict)

    @property
    def settings(self):
        return self.config.get_settings()

    def makedirs(self, key):
        '''Creates a directory if it does not yet exist.
        The argument is a string that may contain one of these placeholders:
        {here} or {up}.
        '''
        makedirs(key.format(here=self.directory, up=self.parent_directory))

    def log(self, text):
        '''TODO: Implement logging setup'''
        print(text)

    def enable_handlers(self, scan=True):
        '''Pyramid "handlers" emulate Pylons 1 "controllers".
        https://github.com/Pylons/pyramid_handlers
        '''
        from pyramid_handlers import includeme
        self.config.include(includeme)
        self.handlers = True

    def enable_sqlalchemy(self, initialize_sql=None):
        from sqlalchemy import engine_from_config
        self.engine = engine = engine_from_config(self.settings, 'sqlalchemy.')
        if initialize_sql is None:
            from importlib import import_module
            try:
                module = import_module(self.name + '.models')
            except ImportError as e:
                self.log('Could not find the models module.')
            else:
                try:
                    initialize_sql = module.initialize_sql
                except AttributeError as e:
                    self.log('initialize_sql() does not exist.')
        if initialize_sql:
            self.log('initialize_sql()')
            initialize_sql(engine, settings=self.settings)

    def enable_turbomail(self):
        from turbomail.control import interface
        import atexit
        options = {key: self.settings[key] for key in self.settings \
            if key.startswith('mail.')}
        interface.start(options)
        atexit.register(interface.stop, options)

    def enable_kajiki(self):
        '''Allows you to use the Kajiki templating language.'''
        from mootiro_web.pyramid_kajiki import renderer_factory
        for extension in ('.txt', '.xml', '.html', '.html5'):
            self.config.add_renderer(extension, renderer_factory)

    def enable_genshi(self):
        '''Allows us to use the Genshi templating language.
        We intend to switch to Kajiki down the road, therefore it would be
        best to avoid py:match.
        '''
        self.settings.setdefault('genshi.translation_domain', self.name)
        from mootiro_web.pyramid_genshi import enable_genshi
        enable_genshi(self.config)

    def enable_deform(self, template_dirs):
        from .pyramid_deform import setup
        setup(template_dirs)

    def configure_favicon(self, path='static/icon/32.png'):
        from mimetypes import guess_type
        from pyramid.resource import abspath_from_resource_spec
        self.settings['favicon'] = path = abspath_from_resource_spec(
            self.settings.get('favicon', '{}:{}'.format(self.name, path)))
        self.settings['favicon_content_type'] = guess_type(path)[0]

    def enable_internationalization(self, extra_translation_dirs):
        self.makedirs(self.settings.get('dir_locale', '{here}/locale'))
        self.config.add_translation_dirs(self.name + ':locale',
            *extra_translation_dirs)
        # from pyramid.i18n import default_locale_negotiator
        # self.config.set_locale_negotiator(default_locale_negotiator)

    def set_template_globals(self, fn=None):
        '''Intended to be overridden in subclasses.'''
        from pyramid import interfaces
        from pyramid.events import subscriber
        from pyramid.i18n import get_localizer, get_locale_name
        from pyramid.url import route_url, static_url
        package_name = self.name

        def template_globals(event):
            '''Adds stuff we use all the time to template context.
            There is no need to add *request* since it is already there.
            '''
            request = event['request']
            settings = request.registry.settings
            # A nicer "route_url": no need to pass it the request object.
            event['url'] = lambda name, *a, **kw: \
                                  route_url(name, request, *a, **kw)
            event['base_path'] = settings.get('base_path', '/')
            event['static_url'] = lambda s: static_url(s, request)
            event['locale_name'] = get_locale_name(request)  # to set xml:lang
            event['enabled_locales'] = settings['enabled_locales']
            # http://docs.pylonsproject.org/projects/pyramid_cookbook/dev/i18n.html
            localizer = get_localizer(request)
            translate = localizer.translate
            pluralize = localizer.pluralize
            event['_'] = lambda text, mapping=None: \
                         translate(text, domain=package_name, mapping=mapping)
            event['plur'] = lambda singular, plural, n, mapping=None: \
                            pluralize(singular, plural, n,
                                      domain=package_name, mapping=mapping)

        self.config.add_subscriber(fn or template_globals,
                                   interfaces.IBeforeRender,
        )

    def result(self):
        '''Commits the configuration (this causes some tests) and returns the
        WSGI application.
        '''
        if self.handlers:
            self.config.scan(self.name)
            for p in self.packages:
                self.config.scan(p)
        return self.config.make_wsgi_app()

    @property
    def all_routes(self):
        '''Returns a list of the routes configured in this application.'''
        return all_routes(self.config)

    def require_python27(self):
        '''Demand Python 2.7 (ensure not trying to run it on 2.6.).'''
        from sys import version_info, exit
        version_info = version_info[:2]
        if version_info < (2, 7) or version_info >= (3, 0):
            exit('\n' + self.name + ' requires Python 2.7.x.')


def all_routes(config):
    '''Returns a list of the routes configured in this application.'''
    return [(x.name, x.pattern) for x in \
            config.get_routes_mapper().get_routes()]
