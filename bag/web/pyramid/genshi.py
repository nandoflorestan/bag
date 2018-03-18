"""Genshi integration for Pyramid.

This module allows the Genshi templating language --
http://pypi.python.org/pypi/Genshi/
-- to be used in the Pyramid web framework --
http://docs.pylonshq.com/

To enable this extension, just include it as your app starts up:

.. code-block:: python

    config.include('bag.web.pyramid.genshi')

Then you can decorate your views like the other Pyramid templating languages,
passing an asset specification to the ``renderer`` argument::

    @view_config(route_name='faq', renderer='mial:templates/faq-page.genshi')

Configuring a set of template directories
=========================================

You don't need to do this. But if you would like to
provide only the file name (without a path) to the renderer, like this::

    @view_config(route_name='faq', renderer='faq-page.genshi')

...then you must set ``genshi.directories`` in the application section
of your Pyramid application’s .ini file::

    [app:myapp]
    # ... other stuff ...
    genshi.directories = myapp:templates
                         myapp:another/templates/directory

This configures a set of directories that are searched.
The portion of each directory argument before the colon is a
package name. The remainder is a subpath within the package which
houses the templates.

But I have optimized for asset specifications. The renderer name is interpreted
first as an asset specification, then if the file is not found,
the directories are searched.

Other settings
==============

You can configure these rendering parameters::

    genshi.doctype = html5
    genshi.method = xhtml

You can also set the file extension that triggers the Genshi renderer.
The default is ".genshi"::

    genshi.extension = .genshi

The Genshi template loader keeps templates cached in memory. You can control
the size of this LRU cache through this setting (my default is 100)::

    genshi.max_cache_size = 100

Finally, internationalization of Genshi templates is enabled by the value of
``genshi.translation_domain``. By default it is the name of your
application package.

    genshi.translation_domain = myapp

Rendering a page fragment
=========================

From anywhere in your web app you can use the renderer like this::

    some_html = settings['genshi_renderer'].fragment(
        'myapp:templates/menu.genshi', template_context_dict)
"""

from os import path
from bag.settings import asbool
from zope.interface import implementer
from pyramid.interfaces import ITemplateRenderer
from pyramid.resource import abspath_from_resource_spec


def to_list(sequence):
    return [sequence] if isinstance(sequence, str) else sequence


def load_template(asset):
    """Make the Genshi TemplateLoader work with typical Pyramid
    asset specifications by passing this function to
    the TemplateLoader constructor as one of the paths.
    """
    # print('LOAD {}'.format(asset))
    abspath = abspath_from_resource_spec(asset)
    stream = open(abspath, 'r')  # Genshi catches the possible IOError.
    mtime = path.getmtime(abspath)
    filename = path.basename(abspath)

    def file_not_changed():
        # debug = 'SAME' if mtime == path.getmtime(abspath) else 'MODIFIED'
        # print(debug, abspath)
        return mtime == path.getmtime(abspath)
    return (abspath, filename, stream, file_not_changed)


@implementer(ITemplateRenderer)
class GenshiTemplateRenderer:
    def __init__(self, settings):
        dirs = settings.get('genshi.directories', [])
        paths = [abspath_from_resource_spec(p) for p in to_list(dirs)]
        paths.insert(0, load_template)  # enable Pyramid asset specifications

        # http://genshi.edgewall.org/wiki/Documentation/i18n
        # If genshi.translation_domain has a value,
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

        from genshi.template import TemplateLoader
        self.loader = TemplateLoader(
            paths, callback=callback,
            auto_reload=asbool(settings.get('pyramid.reload_templates')),
            max_cache_size=int(settings.get('genshi.max_cache_size', 100)))
        self.strip_whitespace = settings.get('genshi.strip_whitespace', True)
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
        rn = system.get('renderer_name') or system['renderer_info'].name
        template = self.loader.load(rn)
        # Mix the *system* and *value* dictionaries
        try:
            system.update(value)
        except (TypeError, ValueError):
            raise ValueError('GenshiTemplateRenderer was passed a '
                             'non-dictionary as value.')
        # Render the template and return a string
        return template.generate(**system) \
            .render(method=self.method,
                    encoding=None,  # so Genshi outputs a unicode object
                    doctype=self.doctype,
                    strip_whitespace=self.strip_whitespace)

    def fragment(self, template, dic):
        """Loads a Genshi template and returns its output as a unicode object
        containing an HTML fragment, taking care of some details.

        * template is the Genshi template file to be rendered.
        * dic is a dictionary to populate the template instance.
        """
        t = self.loader.load(template)
        return t.generate(**dic).render(method=self.method, encoding=None)


def includeme(config):
    """Easily integrate Genshi template rendering into Pyramid."""
    if hasattr(config, 'bag_genshi_included'):
        return  # Include only once per config
    config.bag_genshi_included = True

    settings = config.get_settings()
    # By default, the translation domain is the application name:
    settings.setdefault('genshi.translation_domain', config.registry.__name__)
    # TODO: Evaluate pyramid_genshi which maps to TranslationString calls.

    # The renderer must be available to views so fragment templates can be
    # rendered. So we store it in the settings object:
    renderer = settings['genshi_renderer'] = GenshiTemplateRenderer(settings)

    def factory(info):
        """info.name is the value passed by the user as the renderer name.

        info.package is the "current package" when the renderer configuration
        statement was found.

        info.type is the renderer type name, i.e. ".genshi".

        info.registry is the "current" application registry when
        the renderer was created.

        info.settings is the ISettings dictionary related to the current app.
        """
        return renderer
    extension = settings.get('genshi.extension', '.genshi')
    config.add_renderer(extension, factory)
