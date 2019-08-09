"""Integration of :py:mod:`bag.web.burla` into Pyramid.

Burla provides powerful URL generation independent of web frameworks.

From this module you can import the variable ``ops`` and then use it to
register pages and operations with burla.

burla can autogenerate documentation for those registered pages and operations.

Finally, burla can register them as Pyramid views. For this you need to add,
to the bottom of your Pyramid initialization, this call::

    ops.register_pyramid_views()

TODO: Use the registry instead of a global variable "ops".
"""

from pyramid.response import Response

from bag.web.burla import Burla
try:
    from bag.web.pyramid import _
except ImportError:
    _ = str  # and i18n is disabled.


class PyramidBurla(Burla):
    """Subclass of Burla for integration with Pyramid."""

    def op(self, op_name, section='Miscellaneous', **kw):
        """Decorator to register an API operation.

        Decorate your view handlers with this to register an operation
        with Burla as well as with Pyramid.
        """
        def wrapper(view_handler):
            self._add_op(op_name, section=section, fn=view_handler, **kw)
            return view_handler
        return wrapper

    def page(self, op_name, section='Miscellaneous', **kw):
        """Decorator to register a page.

        Decorate your view handlers with this to register a page
        with Burla as well as with Pyramid.
        """
        def wrapper(view_handler):
            self._add_page(op_name, section=section, fn=view_handler, **kw)
            return view_handler
        return wrapper

    def register_pyramid_views(self):
        """Optionally register all those URLs with Pyramid as views, too."""
        for name, obj in self.map.items():
            if obj.fn:
                # print('REGISTER', name, obj.url_templ)
                self.config.add_view(
                    view=obj.fn,
                    permission=obj.permission,
                    **obj.view_args)
            # else:
                # print('IGNORE  ', name, obj.url_templ)


ops = PyramidBurla()
js_content = None  # populated lazily


def add_http_operations_list_url(config, url='/http_operations'):
    """Add a view that returns pages and HTTP operations as JSON."""
    NAME = 'List operations'
    config.add_route(NAME, url)

    @ops.op(NAME, section='Infrastructure', url_templ=url,
            request_method='GET', route_name=NAME, renderer='json')
    def list_http_operations(context, request):
        """Describe all available application pages and HTTP API operations."""
        return ops.to_dict()


def add_view_for_javascript_file(config, url='/burla'):  # noqa
    NAME = 'Burla JS module'
    config.add_route(NAME, url)

    @ops.op(NAME, section='Infrastructure', url_templ=url,
            request_method='GET', route_name=NAME, renderer='string')
    def javascript_burla_file(context, request):
        """Return the Javascript burla module.

        It contains the available pages and HTTP API operations as well as
        functions to generate corresponding URLs.
        """
        request.response.content_type = 'application/javascript'
        global js_content
        if not js_content:
            js_content = ops.get_javascript_code()
        return js_content


def add_api_doc_view(config, url: str = '/doc_api', **kw) -> None:
    """Add to a Pyramid web app a URL documenting its API."""
    _add_doc_view(config, pages=False, name=Burla.API_TITLE, url=url, **kw)


def _add_doc_view(
    config, name: str, url: str, title: str = '', pages: bool = False,
    prefix: str = '', suffix: str = '',
) -> None:
    from docutils.core import publish_string
    config.add_route(name, url)

    @ops.page(name, section='Infrastructure', url_templ=url, route_name=name)
    def documentation_view(context, request):
        """Page that documents all available URLs."""
        content = publish_string(
            '\n'.join(ops.gen_documentation(
                pages=pages, title=title, prefix=prefix, suffix=suffix)),
            settings_overrides={'output_encoding': 'unicode'},
            writer_name='html')
        return Response(body=content)


def add_pages_doc_view(config, url: str = '/doc_pages', **kw) -> None:
    """Add to a Pyramid web app a URL with its site map."""
    _add_doc_view(config, pages=True, name=Burla.PAGES_TITLE, url=url, **kw)


def includeme(config):
    """Add 2 URLs to a Pyramid web application.

    - **/http_operations**: JSON list of endpoints.
    - **/burla**: Javascript library to generate URLs using the above.
    """
    ops.config = config

    # The request object will be able to generate URLs
    config.add_request_method(ops.url, 'burl')

    add_http_operations_list_url(config)
    add_view_for_javascript_file(config)
