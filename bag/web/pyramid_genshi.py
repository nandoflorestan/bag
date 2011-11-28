#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''This module allows the Genshi templating language --
http://pypi.python.org/pypi/Genshi/
-- to be used in the Pyramid web framework --
http://docs.pylonshq.com/

To enable the pyramid_genshi extension:

    from mootiro_web.pyramid_genshi import enable_genshi
    enable_genshi(config, extension='.genshi')

...where `config` is your Configurator instance, and `extension` is
the file extension you are using for your templates.

Once the extension is active, add the following to the application section
of your Pyramid application’s .ini file:

    [app:yourapp]
    # ... other stuff ...
    genshi.directories = myapp:templates
                         myapp:another/templates/directory

This configures the set of directories searched.
The portion of each directory argument before the colon is a
package name. The remainder is a subpath within the package which
houses the templates.
Adding more than one directory forms a search path.

Then you should decorate your views like this, passing only the file name
(no path):

    @action(renderer='root.genshi')

You can also configure these rendering parameters:

    genshi.encoding = utf-8
    genshi.doctype = html5
    genshi.method = xhtml

Finally, you can enable internationalization of Genshi templates by
configuring "genshi.translation_domain". Usually the value is your
application name. This adds a translation filter:

    genshi.translation_domain = SomeDomain
'''

from __future__ import unicode_literals # unicode by default

from paste.deploy.converters import asbool
from zope.interface import implements
from zope.interface import Interface
from pyramid.interfaces import ITemplateRenderer
from pyramid.resource import abspath_from_resource_spec


def to_list(sequence):
    if isinstance(sequence, basestring):
        return [sequence]
    else:
        return sequence


class GenshiTemplateRenderer(object):
    implements(ITemplateRenderer)

    def __init__(self, settings):
        from genshi.template import TemplateLoader
        try:
            dirs = settings['genshi.directories']
        except KeyError:
            raise KeyError('You need to configure genshi.directories.')
        paths = [abspath_from_resource_spec(p) for p in to_list(dirs)]
        # http://genshi.edgewall.org/wiki/Documentation/i18n.html
        # If genshi.translation_domain is configured,
        # we set up a callback in the loader
        domain = settings.get('genshi.translation_domain')
        if domain:
            from genshi.filters import Translator
            from pyramid.i18n import get_localizer
            from pyramid.threadlocal import get_current_request
            def translate(text):
                return get_localizer(get_current_request()) \
                       .translate(text, domain=domain)
            def callback(template):
                Translator(translate).setup(template)
        else:
            callback = None
        self.loader = TemplateLoader(paths,
                      auto_reload = asbool(settings.get('reload_templates')),
                      callback = callback)
        self.strip_whitespace = settings.get('genshi.strip_whitespace', True)
        self.encoding = settings.get('genshi.encoding', 'utf-8')
        self.doctype = settings.get('genshi.doctype', 'html5')
        self.method = settings.get('genshi.method', 'xhtml')

    def implementation(self):
        return self

    def __call__(self, value, system):
        """ ``value`` is the result of the view.
        Returns a result (a string or unicode object useful as
        a response body). Values computed by
        the system are passed by the system in the ``system``
        parameter, which is a dictionary. Keys in the dictionary
        include: ``view`` (the view callable that returned the value),
        ``renderer_name`` (the template name or simple name of the
        renderer), ``context`` (the context object passed to the
        view), and ``request`` (the request object passed to the
        view).
        """
        template = self.loader.load(system['renderer_name'])
        # Mix the *system* and *value* dictionaries
        try:
            system.update(value)
        except (TypeError, ValueError):
            raise ValueError('GenshiTemplateRenderer was passed a '
                             'non-dictionary as value.')
        # Render the template and return a string
        return template.generate(**system) \
            .render(method=self.method,
                    encoding=self.encoding,
                    doctype=self.doctype,
                    strip_whitespace=self.strip_whitespace)

    def fragment(self, template_file, dic):
        """Loads a Genshi template and returns its output as a unicode object
        containing an HTML fragment, taking care of some details.

        - template_file is the name of the Genshi template file to be rendered.
        - dic is a dictionary to populate the template instance.
        """
        t = self.loader.load(template_file)
        # encoding=None makes Genshi return a unicode object:
        return t.generate(**dic) \
            .render(method=self.method, encoding=None)



def enable_genshi(config, extension='.genshi'):
    '''Allows us to use the Genshi templating language in Pyramid.
    '''
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
        return info.settings['genshi_renderer']
    settings = config.get_settings()
    settings['genshi_renderer'] = GenshiTemplateRenderer(settings)
    config.add_renderer(extension, renderer_factory)
