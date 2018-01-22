# -*- coding: utf-8 -*-

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

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from nine import IS_PYTHON2, nimport, nine, range, str, basestring
from bag.web.burla import Burla, DOC_TITLE
from pyramid.response import Response


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
    NAME = 'List operations'
    config.add_route(NAME, url)

    @ops.op(NAME, section='Infrastructure', url_templ=url,
            request_method='GET', route_name=NAME, renderer='json')
    def list_http_operations(context, request):
        """Describe all available application pages and HTTP API operations."""
        return ops.to_dict()


def add_view_for_javascript_file(config, url='/burla'):
    NAME = 'Burla JS module'
    config.add_route(NAME, url)

    @ops.op(NAME, section='Infrastructure', url_templ=url,
            request_method='GET', route_name=NAME, renderer='string')
    def javascript_burla_file(context, request):
        """Javascript file that contains the available pages and HTTP API
        operations as well as functions to generate corresponding URLs.
        """
        request.response.content_type = 'application/javascript'
        global js_content
        if not js_content:
            js_content = ops.get_javascript_code()
        return js_content


def add_view_for_documentation(config, url='/api_docs', title=None,
                               prefix=None, suffix=None):
    from docutils.core import publish_string
    config.add_route(DOC_TITLE, url)

    @ops.page(DOC_TITLE, section='Infrastructure', url_templ=url,
              route_name=DOC_TITLE)
    def api_documentation_view(context, request):
        """Displays all available HTTP API methods."""
        content = publish_string(
            '\n'.join(ops.gen_documentation(
                title=title, prefix=prefix, suffix=suffix)),
            settings_overrides={'output_encoding': 'unicode'},
            writer_name='html')
        return Response(body=content)


def includeme(config):
    """Hook for Pyramid; adds 2 URLs to your application.

    - **/http_operations**: JSON list of endpoints.
    - **/burla**: Javascript library to generate URLs using the above.
    """
    ops.config = config

    # The request object will be able to generate URLs
    config.add_request_method(ops.url, 'burl')

    add_http_operations_list_url(config)
    add_view_for_javascript_file(config)
    # add_view_for_documentation(config)
