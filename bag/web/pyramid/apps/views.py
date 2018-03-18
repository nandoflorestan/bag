"""Useful base views, functions and decorators for Pyramid."""

from typing import Any, Dict  # noqa
from pyramid.decorator import reify
from pyramid.i18n import get_localizer
from pyramid.renderers import get_renderer
from pyramid.url import route_url
from bag.settings import asbool
from bag.text import uncommafy


class BaseView:
    """Base class for views."""

    def __init__(self, request):
        self.request = request

    @reify
    def tr(self):
        """The translator of the localizer of this request."""
        return get_localizer(self.request).translate

    def url(self, name, *a, **kw):
        """A route_url that is easier to use."""
        return route_url(name, self.request, *a, **kw)


undefined = object()


class BaseViewForDeform(BaseView):

    def model_to_dict(self, model, key_provider):
        """Return an appstruct dict with values taken from the ``model``.

        *key_provider* can be:

        * a comma-delimited string of key names,
        * a list of strings representing key names,
        * a colander.Schema (or subclass).
        """
        import colander as c
        d = {}

        if isinstance(key_provider, str):
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
        """Update ``model`` with ``adict``."""
        import colander as c
        for key, val in adict.items():
            setattr(model, key, None if val is c.null else val)
        return model


class ChameleonBaseView:
    """Base view mixin class for projects that use Chameleon with macros."""

    macro_cache = {}  # type: Dict[str, Any]  # for Chameleon template macros

    def macro(self, template, macro_name):
        """Load macros from any Chameleon template.

        If settings['reload_templates'] is false, also memoize the macros.
        """
        if asbool(self.request.registry.settings.get('reload_templates')):
            return get_renderer(template).implementation().macros[macro_name]
        else:
            macro_path = template + '|' + macro_name
            macro = self.macro_cache.get(macro_path)
            if not macro:
                self.macro_cache[macro_path] = macro = \
                    get_renderer(template).implementation().macros[macro_name]
            return macro
