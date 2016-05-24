# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import os
import stat
from nine import str
from pyramid.resource import abspath_from_resource_spec
from pyramid.response import FileResponse
from ...log import setup_log
from .plugins_manager import PluginsManager, BasePlugin


def isdir(s):
    """Return true if the pathname refers to an existing directory."""
    try:
        st = os.stat(s)
    except os.error:
        return False
    return stat.S_ISDIR(st.st_mode)


def makedirs(s):
    """Make directories (if they don't exist already)."""
    if not isdir(s):
        os.makedirs(s)


def register_view_class(cls):
    """Class decorator that adds the class to a list."""
    view_classes.append(cls)
    return cls
view_classes = []


def subdict(adict, prefix):
    """Return a new dict based on keys that start with a prefix."""
    lprefix = len(prefix)
    return {key[lprefix:]: val for key, val in adict.items()
            if key.startswith(prefix)}


class PyramidStarter(object):
    """Reusable configurator for nice Pyramid applications."""

    def __init__(self, config, packages=[], log=None):
        """Arguments:

        * *config* is the Pyramid configurator instance.
        * *packages* is a sequence of additional packages that should be
        scanned/enabled.
        """
        self.package_name = config.package.__name__
        self.require_python_version()
        self.config = config
        if 'app.name' not in self.settings:
            raise KeyError(
                'Your configuration files are missing an "app.name" setting.')
        # Add self to config so other applications can find it
        config.bag = self
        self.packages = packages
        self.directory = os.path.abspath(
            os.path.dirname(config.package.__file__))
        self.parent_directory = os.path.dirname(self.directory)
        self.makedirs('{here}/locale')
        config.add_translation_dirs('bag:locale')
        self.log = log or setup_log(name='PyramidStarter')

    @property
    def settings(self):
        return self.config.get_settings()

    def makedirs(self, key):
        """Create a directory if it does not yet exist.

        The argument is a string that may contain one of these placeholders:
        {here} or {up}.
        """
        makedirs(key.format(here=self.directory, up=self.parent_directory))

    def enable_handlers(self):
        """Pyramid "handlers" emulate Pylons 1 "controllers".
        This is deprecated because Pyramid is now more powerful.

        https://github.com/Pylons/pyramid_handlers
        """
        from warnings import warn
        warn(
            'enable_handlers() is deprecated. Pyramid 1.3 does not need them.')
        from pyramid_handlers import includeme
        self.config.include(includeme)
        self.scan()

    def enable_sqlalchemy(self, initialize_sql=None):
        # Looks like ptah.ptahsettings.initialize_sql() does more or less
        # the same thing. Don't call this if you use Ptah.
        from sqlalchemy import engine_from_config
        settings = self.settings
        self.engine = engine = engine_from_config(settings, 'sqlalchemy.')
        if initialize_sql is None:
            from importlib import import_module
            try:
                module = import_module(self.package_name + '.models')
            except ImportError:
                self.log.warn('Could not find the models module.')
            else:
                try:
                    initialize_sql = module.initialize_sql
                except AttributeError:
                    self.log.warn('initialize_sql() does not exist.')
        if initialize_sql:
            self.log.info('initialize_sql()')
            initialize_sql(engine, settings=settings)
        registry = self.config.registry
        if hasattr(registry, 'plugins'):
            registry.plugins.call('initialize_sql', dict(
                engine=engine, settings=settings))

    @classmethod
    def init_basic_sqlalchemy(cls):
        """Return a declarative base class and a SQLAlchemy scoped session
        that uses the ZopeTransactionExtension.
        """
        from sqlalchemy.orm import scoped_session, sessionmaker
        from zope.sqlalchemy import ZopeTransactionExtension
        sas = scoped_session(sessionmaker(
            extension=ZopeTransactionExtension()))
        from sqlalchemy.ext.declarative import declarative_base
        Base = declarative_base()
        return Base, sas

    def enable_marrow_mailer(self):
        """Enable https://github.com/marrow/marrow.mailer

        After this you can access registry.mailer to send messages.
        """
        from marrow.mailer import Mailer
        import atexit
        options = subdict(self.settings, 'marrow.mailer.')
        mailer = self.config.registry.mailer = Mailer(options)
        mailer.start()
        atexit.register(mailer.stop)
        if hasattr(self.config, 'ptah_init_mailer'):
            # If using Ptah, instead of installing another mailer for it,
            # we can still send simple messages with the following hack.
            class Sender(object):                 # Provide Ptah with an object
                def send(self, author, to, msg):  # that has a send() method.
                    from quopri import decodestring
                    m = mailer.new(
                        to=to, subject=str(msg['subject']),
                        plain=decodestring(msg.get_payload()))
                    mailer.send(m)
            self.config.ptah_init_mailer(Sender())

    def enable_favicon(self, path='static/favicon.ico'):
        """Register a view that serves /favicon.ico.

        web_deps.PageDeps contains a favicon_tag() method that you can use to
        create the link to it.

        FileResponse appeared in Pyramid 1.3a9.
        """
        path = abspath_from_resource_spec(self.package_name + ':' + path)

        def favicon_view(request):
            return FileResponse(path, request=request)
        self.config.add_route('favicon', 'favicon.ico')
        self.config.add_view(favicon_view, route_name='favicon')

    def enable_robots(self, path='static/robots.txt'):
        """Read robots.txt into memory, then set up a view that serves it."""
        from mimetypes import guess_type
        path = abspath_from_resource_spec(
            self.settings.get('robots', '{}:{}'.format(
                self.package_name, path)))
        content_type = guess_type(path)[0]
        import codecs
        with codecs.open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        from pyramid.response import Response

        def robots_view(request):
            return Response(content_type=content_type, app_iter=content)
        self.config.add_route('robots', '/robots.txt')
        self.config.add_view(robots_view, route_name='robots')

    def set_template_globals(self, fn=None):
        """Prepare a subscriber to IBeforeRender that adds
        very useful variables to the template context dictionary.

        You can customize this by passing a function in.
        """
        from pyramid import interfaces
        from pyramid.i18n import get_localizer
        from pyramid.url import route_url, static_url
        package_name = self.package_name

        def template_globals(event):
            """Adds stuff we use all the time to template context.
            There is no need to add *request* since it is already there.
            """
            request = event['request']
            settings = request.registry.settings
            # A nicer "route_url": no need to pass it the request object.
            event['url'] = lambda name, *a, **kw: \
                route_url(name, request, *a, **kw)
            event['base_path'] = settings.get('base_path', '/')
            event['static_url'] = lambda s: static_url(s, request)
            event['appname'] = settings.get('app.name', 'Application')
            localizer = get_localizer(request)
            translate = localizer.translate
            pluralize = localizer.pluralize
            event['_'] = lambda text, mapping=None: \
                translate(text, domain=package_name, mapping=mapping)
            event['plur'] = lambda singular, plural, n, mapping=None: \
                pluralize(singular, plural, n,
                          domain=package_name, mapping=mapping)

        self.config.add_subscriber(fn or template_globals,
                                   interfaces.IBeforeRender)

    def declare_routes_from_views(self):
        self.scan()  # in order to find all the decorated view classes
        for k in view_classes:
            if hasattr(k, 'declare_routes'):
                k.declare_routes(self.config)

    def declare_deps_from_views(self, deps, rooted):
        self.scan()  # in order to find all the decorated view classes
        settings = self.settings
        for k in view_classes:
            if hasattr(k, 'declare_deps'):
                k.declare_deps(deps, rooted, settings)

    def scan(self):
        self.packages.append(self.package_name)
        for p in self.packages:
            self.config.scan(p)
            locale_dir = abspath_from_resource_spec(p + ':locale')
            if os.path.isdir(locale_dir):
                self.config.add_translation_dirs(locale_dir)
        # Make this method a noop for the future (scan only once)
        self.scan = lambda: None

    def result(self):
        """Commit the configuration and return the WSGI application."""
        return self.config.make_wsgi_app()

    @property
    def all_routes(self):
        """Return a list of the routes configured in this application."""
        return all_routes(self.config)

    def require_python_version(self):
        """Demand Python 2.7 or > 3.2."""
        from sys import version_info, exit
        version_info = version_info[:2]
        if version_info < (2, 7) or (3, 0) <= version_info < (3, 2):
            exit('\n' + self.package_name + ' requires Python 2.7.x or > 3.2.')

    def load_plugins(self, entry_point_groups=None, directory=None,
                     base_class=BasePlugin):
        self.config.registry.plugins = self.plugins = \
            PluginsManager(self.settings)
        if directory:
            self.plugins.find_directory_plugins(directory,
                                                plugin_class=base_class)
        if entry_point_groups:
            self.plugins.find_egg_plugins(entry_point_groups)


def all_routes(config):
    """Return a list of the routes configured in this application."""
    return [(x.name, x.pattern) for x in
            config.get_routes_mapper().get_routes()]


def all_views(registry):
    return set([o['introspectable']['callable']
                for o in registry.introspector.get_category('views')])


def all_view_classes(registry):
    # I have left this code here, but it is better to just use the
    # @register_view_class decorator and then look up the view_classes list.
    return [o for o in all_views(registry) if isinstance(o, type)]


def authentication_policy(
        settings, include_ip=True, timeout=60 * 60 * 32,
        reissue_time=60, groupfinder=lambda userid, request: []):
    """Return an authentication policy object for configuration."""
    try:
        secret = settings['cookie_salt']
    except KeyError:
        raise KeyError('Your config file is missing a cookie_salt.')
    from pyramid.authentication import AuthTktAuthenticationPolicy
    return AuthTktAuthenticationPolicy(
        secret, callback=groupfinder,
        include_ip=include_ip, timeout=timeout, reissue_time=reissue_time)
