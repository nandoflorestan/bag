"""Kajiki integration for Pyramid.

This module allows the Kajiki templating language --
http://pypi.python.org/pypi/Kajiki/
-- to be used in the Pyramid web framework --
http://docs.pylonshq.com/

To enable the pyramid_kajiki extension, do this:

.. code-block:: python

    config.include('bag.web.pyramid.kajiki')

Once the template loader is active, add the following to the
application section of your Pyramid application’s .ini file::

    [app:yourapp]
    # ... other stuff ...
    kajiki.directory = myapp:templates
    kajiki.extensions = .kajiki .genshi .html

The Kajiki FileLoader class supports searching only one directory for
templates. If you want a search path, you must roll your own.
If you do... let us know.
"""

from bag.settings import asbool
from zope.interface import implementer
from pyramid.interfaces import ITemplateRenderer
from pyramid.resource import abspath_from_resource_spec

from warnings import warn
warn('Kajiki now has kajiki.integration.pyramid!', DeprecationWarning)


@implementer(ITemplateRenderer)
class KajikiTemplateRenderer(object):

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
    """*info* contains:

    ::

        name = Attribute('The value passed by the user as the renderer name')
        package = Attribute('The "current package" when the renderer '
                            'configuration statement was found')
        type = Attribute('The renderer type name')
        registry = Attribute('The "current" application registry when the '
                             'renderer was created')
        settings = Attribute('The ISettings dictionary related to the '
                             'current app')
    """
    registry = info.registry
    settings = info.settings
    if not hasattr(registry, 'kajiki_loader'):
        from kajiki import FileLoader
        registry.kajiki_loader = FileLoader(
            base=abspath_from_resource_spec(settings['kajiki.directory']),
            reload=asbool(settings.get('reload_templates')),
            force_mode=asbool(settings.get('kajiki.force_mode')),
            autoescape_text=asbool(settings.get('kajiki.autoescape')),
        )
    return KajikiTemplateRenderer(info)


def includeme(config):
    """Set up Kajiki templating for the configured file extensions."""
    if hasattr(config, 'bag_kajiki_included'):
        return  # Include only once per config
    config.bag_kajiki_included = True

    settings = config.get_settings()
    extensions = settings.get('kajiki.extensions', '.kajiki').split()
    for extension in extensions:
        config.add_renderer(extension, renderer_factory)
