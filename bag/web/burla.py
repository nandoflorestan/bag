# -*- coding: utf-8 -*-

"""Powerful URL generation independent of web frameworks.

**Burla** stores a collection of page URL templates, separate from a
collection of API method URL templates.  The only difference between
them is that operations have a request method (GET, POST, PUT etc.).

Burla also facilitates generating documentation about pages and
API operations in the Python server.

No matter what web framework you are using, you are better off
generating URLs with Burla because this makes your application more
independent of web frameworks so you can switch more easily.

Another advantage is that, based on the URL templates, burla generates
URLs in the Python server as well as in the Javascript client.  It
generates a short Javascript library that takes care of this.

Maintenance of your web app becomes easier because you register your
URLs only once (in the Python server code) and then the URLs can be
used in the entire stack.  When you change your URLs, you only do it
in one place.

URL templates (for matching views) stop at the left of the question mark,
but when generating URLs, burla supports both query params
(to the right of the question mark) and fragments (to the right of the #),

Here are a few examples of usage in the Javascript client:

.. code-block:: javascript

    // Let's see a previously registered URL template:
    burla.page('User details')
    "/users/:user_id/details"

    // Provide a map to generate a real URL from the template:
    burla.page('User details', {user_id: 1})
    "/users/1/details"

    // Provide another argument to add a fragment (to the right of the #):
    burla.page('User details', {user_id: 1}, 'tab=aboutme')
    "/users/1/details#tab=aboutme"

    // Extra params (not found in the URL template) go in the query:
    burla.page('User details', {user_id: 1, photos: 'big'}, 'tab=aboutme')
    "/users/1/details?photos=big#tab=aboutme"

You can find integration with the Pyramid web framework in
:py:mod:`bag.web.pyramid.burla`. Please contribute integration into
other frameworks.
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from collections import OrderedDict
from nine import IS_PYTHON2, nimport, nine, range, str, basestring
from json import dumps
from re import compile

try:
    from bag.web.pyramid import _
except ImportError:
    _ = str  # and i18n is disabled.

urlencode = nimport('urllib.parse:urlencode')


class Page(object):
    """Class that represents a web page in burla.

    A page is comprised of a descriptive name, a URL template (from which
    parameters are discovered) and possibly documentation strings.
    The instance is able to generate its URL.

    A URL template looks like this (params are preceded by a colon)::

        /cities/:city/streets/:street
    """

    def __init__(self, op_name, url_templ, fn=None, permission=None,
                 section='Miscellaneous', **view_args):
        assert isinstance(op_name, basestring)
        assert op_name
        assert isinstance(url_templ, basestring)
        assert url_templ
        self.name = op_name
        self.url_templ = url_templ
        self.fn = fn

        # In Python source the doc will contain extra indentation
        doc = fn.__doc__ if fn else None
        if doc:
            alist = []
            for line in doc.split('\n'):
                alist.append(line[8:] if line.startswith(' ' * 8) else line)
            doc = '\n'.join(alist)
        self.doc = doc  # description of the page or HTTP operation

        self.permission = permission
        self.section = section  # of the documentation
        self.view_args = view_args

        self._discover_params_in_url_templ()

    def _discover_params_in_url_templ(self):
        self.params = []
        for match in self.PARAM.finditer(self.url_templ):
            self.params.append(match.group(1))
    PARAM = compile(r':([a-z_]+)')

    def url(self, fragment='', **kw):
        """Given a dictionary, generate an actual URL from the template."""
        astr = self.url_templ
        for param in self.params:
            key = ':' + param
            if key in self.url_templ:
                value = str(kw.pop(param))
                astr = astr.replace(key, value)
        # The remaining params in kw make the query parameters
        if kw:
            astr += '?' + urlencode(kw)
        if fragment:
            astr += '#' + fragment
        return astr

    def to_dict(self):
        """Convert this instance into a dictionary, maybe for JSON output."""
        return {
            'url_templ': self.url_templ,
            'permission': self.permission,
        }

    is_page = True
    is_operation = not is_page


class Operation(Page):
    """Subclass of Page representing an HTTP operation."""

    def to_dict(self):
        adict = super(Operation, self).to_dict()
        adict['request_method'] = self.view_args.get('request_method')
        return adict

    is_page = False
    is_operation = not is_page


class Burla(object):
    """Collection of pages and operations. Easily output as JSON.

    Generates URLs and provides JS code to generate URLs in the client.
    """

    def __init__(self, root='', page_class=Page, op_class=Operation):
        self.map = OrderedDict()
        self.root = root
        self._page_class = page_class
        self._op_class = op_class

    def _add_page(self, op_name, **kw):
        assert op_name not in self.map, 'Already registered: {}'.format(
            op_name)
        self.map[op_name] = self._page_class(op_name, **kw)

    def _add_op(self, op_name, **kw):
        assert op_name not in self.map, 'Already registered: {}'.format(
            op_name)
        self.map[op_name] = self._op_class(op_name, **kw)

    def url(self, name, **kw):
        """Return only the generated URL."""
        return self.map[name].url(**kw)

    # def item(self, name, **kw):
    #     """Returns the generated URL and the request_method."""
    #     op = self.map[name]
    #     return {'url': op.url(**kw), 'request_method': op.request_method}

    def add_op(self, op_name, **kw):
        """Decorator for view handlers that registers an operation with Burla.
        """
        def wrapper(view_handler):
            self._add_op(op_name, fn=view_handler, **kw)
            return view_handler
        return wrapper

    def add_page(self, op_name, **kw):
        """Decorator for view handlers that registers a page with Burla."""
        def wrapper(view_handler):
            self._add_page(op_name, fn=view_handler, **kw)
            return view_handler
        return wrapper

    def gen_pages(self):
        for o in self.map.values():
            if o.is_page:
                yield o

    def gen_ops(self):
        for o in self.map.values():
            if o.is_operation:
                yield o

    def to_dict(self):
        """Use this to generate JSON so the client knows the URLs too."""
        return {
            'pages': {o.name: o.to_dict() for o in self.gen_pages()},
            'ops': {o.name: o.to_dict() for o in self.gen_ops()},
            }

    def gen_documentation(self, title=None, prefix=None, suffix=None):
        """Generate documentation in reStructuredText.

        Sources of information are the 'section', 'name', 'doc' and
        'permission' attributes of the registered Operation instances.
        """
        # Organize the operations inside their respective sections first
        sections = {}
        for op in self.gen_ops():
            if op.section not in sections:
                sections[op.section] = []
            sections[op.section].append(op)

        if title != '':
            title = title or DOC_TITLE
            title_line = '=' * len(title)
            yield title_line
            yield title
            yield title_line
            yield ''
        if prefix:
            yield prefix
            yield ''
        yield 'API methods'
        yield '~~~~~~~~~~~'
        yield ''

        for section in sorted(sections):
            if section:
                yield section
                yield '=' * len(section)
                yield ''

            section = sections[section]
            for op in sorted(section, key=lambda op: op.name):
                if op.name:
                    yield op.name
                    yield '-' * len(op.name)
                    yield ''
                if op.url_templ:
                    yield '::\n'
                    method = op.view_args.get('request_method')
                    if method:
                        url_line = method + ' ' + op.url_templ
                    else:
                        url_line = op.url_templ
                    yield '    ' + url_line
                    yield ''
                if op.doc:
                    yield op.doc
                    yield ''
                if op.permission:
                    yield 'This method requires that the user have the ' \
                        '"{}" permission.'.format(op.permission)
                    yield ''

        if suffix:
            yield suffix
            yield ''

    def get_javascript_code(self):
        """Return a JS library to generate the application URLs.

        Return JS code containing the registered operations and pages,
        plus functions to generate URLs from them.
        """
        return """"use strict";

// Usage:
// var url = burla.page(pageName, params, fragment);
// var url = burla.op(operationName, params, fragment);

window.burla = {
    root: ROOT,
    pages: PAGES,
    ops: OPERATIONS,

    urlencode: function (adict) {
        return Object.keys(adict).map(function (key) {
            return [key, adict[key]].map(encodeURIComponent).join("=");
        }).join("&");
    },
    _find: function (map, name, params, fragment) {
        var s = map[name].url_templ;
        if (!s)  throw new Error('burla: No item called "' + name + '".');
        var p = {};
        for (var key in params) {
            var placeholder = ':' + key;
            var val = params[key];
            if (s.indexOf(placeholder) == -1) {
                p[key] = val; // accumulate
            } else {
                if (val == null)  throw new Error('burla: Operation "' + name + '" needs parameter "' + key + '".');
                s = s.replace(placeholder, val);
            }
        }
        var strParams = this.urlencode(p);
        if (strParams) s += '?' + strParams;
        if (fragment)  s += '#' + fragment;
        return this.root + s;
    },
    page: function (name, params, fragment) {
        return this._find(this.pages, name, params, fragment);
    },
    op: function (name, params, fragment) {
        return this._find(this.ops, name, params, fragment);
    },
}\n""" \
            .replace('PAGES', dumps(
                {o.name: o.to_dict() for o in self.gen_pages()},
                sort_keys=True)) \
            .replace('OPERATIONS', dumps(
                {o.name: o.to_dict() for o in self.gen_ops()},
                sort_keys=True)) \
            .replace('ROOT', dumps(self.root))

DOC_TITLE = _('HTTP API Documentation')
