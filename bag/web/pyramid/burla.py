# -*- coding: utf-8 -*-

"""Burla integration for Pyramid"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from nine import IS_PYTHON2, nimport, nine, range, str, basestring
from bag.web.burla import Burla, DOC_TITLE
from pyramid.response import Response


class PyramidBurla(Burla):
    def op(self, op_name, url_templ, fn=None, section='Miscellaneous', **kw):
        """Decorator for view handlers that registers an operation with Burla
            as well as with Pyramid.
            """
        def wrapper(view_handler):
            self._add_op(
                op_name,
                url_templ=url_templ,
                section=section,
                fn=view_handler,
                request_method=kw['request_method'],
                permission=kw.get('permission'),
                )
            self.config.add_view(view=view_handler, **kw)
            return view_handler
        return wrapper

    def page(self, op_name, url_templ, fn=None, section='Miscellaneous', **kw):
        """Decorator for view handlers that registers a page with Burla
            as well as with Pyramid.
            """
        def wrapper(view_handler):
            self._add_page(
                name=op_name,
                url_templ=url_templ,
                section=section,
                fn=view_handler,
                permission=kw.get('permission'),
                )
            self.config.add_view(view=view_handler, **kw)
            return view_handler
        return wrapper


ops = PyramidBurla()
js_content = None  # populated lazily


def add_http_operations_list_url(config, url='/http_operations'):
    NAME = 'List operations'
    config.add_route(NAME, url)

    @ops.op(NAME, section='Infrastructure', url_templ=url,
            request_method='GET', route_name=NAME, renderer='json')
    def list_http_operations(context, request):
        """Returns objects containing the available application pages and
            HTTP API operations in JSON format.
            """
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


def add_view_for_documentation(config, url='/api_docs', title=None, prefix=None, suffix=None):
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
    ops.config = config

    # The request object will be able to generate URLs
    config.add_request_method(ops.url, 'burl')

    add_http_operations_list_url(config)
    add_view_for_javascript_file(config)
    # add_view_for_documentation(config)
