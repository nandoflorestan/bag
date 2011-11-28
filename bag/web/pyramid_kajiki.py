#!/usr/bin/env python
# -*- coding: utf-8 -*-
# http://docs.python.org/whatsnew/pep-328.html
from __future__ import absolute_import
from __future__ import print_function   # deletes the print statement
from __future__ import unicode_literals # unicode by default

'''This module allows the Kajiki templating language --
http://pypi.python.org/pypi/Kajiki/
-- to be used in the Pyramid web framework --
http://docs.pylonshq.com/

To enable the pyramid_kajiki extension, do this:

    from mootiro_web.pyramid_kajiki import enable_kajiki
    enable_kajiki(config)

After this, files with these file extensions are considered to be
Kajiki templates: '.txt', '.xml', '.html', '.html5'.

Once the template loader is active, add the following to the
application section of your Pyramid application’s .ini file:

    [app:yourapp]
    # ... other stuff ...
    kajiki.directory = myapp:templates

The Kajiki FileLoader class supports searching only one directory for templates.
As of 2011-01, if you want a search path, you must roll your own.
If you do... let us know.
'''

from paste.deploy.converters import asbool
from zope.interface import implements
from zope.interface import Interface
from pyramid.interfaces import ITemplateRenderer
from pyramid.resource import abspath_from_resource_spec


class KajikiTemplateRenderer(object):
    implements(ITemplateRenderer)

    def __init__(self, info):
        self.loader = info.registry.kajiki_loader

    def implementation(self):
        return self

    def __call__(self, value, system):
        """ ``value`` is the result of the view.
        Returns a result (a string or unicode object useful as a
        response body). Values computed by the system are passed in the
        ``system`` parameter, which is a dictionary containing:

        * ``view`` (the view callable that returned the value),
        * ``renderer_name`` (the template name or simple name of the renderer),
        * ``context`` (the context object passed to the view), and
        * ``request`` (the request object passed to the view).
        """
        Template = self.loader.import_(system['renderer_name'])
        try:
            system.update(value)
        except (TypeError, ValueError):
            raise ValueError('KajikiTemplateRenderer was passed a '
                             'non-dictionary as value.')
        t = Template(system)
        return t.render()


def renderer_factory(info):
    ''' ``info`` contains:
    name = Attribute('The value passed by the user as the renderer name')
    package = Attribute('The "current package" when the renderer '
                        'configuration statement was found')
    type = Attribute('The renderer type name')
    registry = Attribute('The "current" application registry when the '
                         'renderer was created')
    settings = Attribute('The ISettings dictionary related to the '
                         'current app')
    '''
    registry = info.registry
    settings = info.settings
    if not hasattr(registry, 'kajiki_loader'):
        from kajiki import FileLoader
        registry.kajiki_loader = FileLoader( \
            base = abspath_from_resource_spec(settings['kajiki.directory']),
            reload               = asbool(settings.get('reload_templates')),
            force_mode           = asbool(settings.get('kajiki.force_mode')),
            autoescape_text      = asbool(settings.get('kajiki.autoescape')),
        )
    return KajikiTemplateRenderer(info)


def enable_kajiki(config, extensions=('.txt', '.xml', '.html', '.html5')):
    '''Sets up the Kajiki templating language for the specified file extensions.
    '''
    for extension in extensions:
        config.add_renderer(extension, renderer_factory)
