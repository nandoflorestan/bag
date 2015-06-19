# -*- coding: utf-8 -*-

'''Burla integration for Pyramid'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from nine import IS_PYTHON2, nimport, nine, range, str, basestring
from bag.web.burla import Burla, DOC_TITLE
from pyramid.response import Response

ops = Burla()
js_content = None  # populated lazily


def add_http_operations_list_url(config, url='/http_operations'):
    NAME = 'List operations'

    @ops.op(name=NAME, url_templ=url, request_method='GET')
    def list_http_operations(context, request):
        return ops.to_dict()

    config.add_route(NAME, url)
    config.add_view(
        view=list_http_operations, route_name=NAME, renderer='json')


def add_view_for_javascript_file(config, url='/burla'):
    NAME = 'Burla JS module'

    @ops.op(NAME, url_templ=url, request_method='GET')
    def javascript_burla_file(context, request):
        request.response.content_type = 'application/javascript'
        global js_content
        if not js_content:
            js_content = ops.get_javascript_code()
        return js_content

    config.add_route(NAME, url)
    config.add_view(javascript_burla_file, route_name=NAME, renderer='string')


def add_view_for_documentation(config, url='/api_docs', title=None, prefix=None, suffix=None):
    from docutils.core import publish_string

    @ops.op(DOC_TITLE, url_templ=url, request_method='GET')
    def api_documentation_view(context, request):
        content = publish_string(
            '\n'.join(ops.gen_documentation(
                title=None, prefix=None, suffix=None)),
            settings_overrides={'output_encoding': 'unicode'},
            writer_name='html')
        return Response(body=content)

    config.add_route(DOC_TITLE, url)
    config.add_view(api_documentation_view, route_name=DOC_TITLE)


def includeme(config):
    # The request object will be able to generate URLs
    config.add_request_method(ops.url, 'burl')

    add_http_operations_list_url(config)
    add_view_for_javascript_file(config)
    # add_view_for_documentation(config)
