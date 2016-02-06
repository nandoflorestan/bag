# -*- coding: utf-8 -*-

"""Burla: Powerful URL generation independent of web frameworks"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from nine import IS_PYTHON2, nimport, nine, range, str, basestring
from json import dumps
from re import compile

try:
    from bag.web.pyramid import _
except ImportError:
    _ = str  # and i18n is disabled.


class Page(object):
    """A page is comprised of a descriptive name, a URL template (from which
        parameters are discovered) and possibly documentation strings.
        The instance is able to generate its URL.

        A URL template looks like this (params are preceded by a colon)::

            /cities/:city/streets/:street
        """

    def __init__(self, name, url_templ, fn=None, permission=None,
                 section='Miscellaneous', **kw):
        assert isinstance(name, basestring)
        assert name
        assert isinstance(url_templ, basestring)
        assert url_templ
        self.name = name
        self.url_templ = url_templ

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
        for k, v in kw.items():
            setattr(self, k, v)
        self._discover_params_in_url_templ()

    def _discover_params_in_url_templ(self):
        self.params = []
        for match in self.PARAM.finditer(self.url_templ):
            self.params.append(match.group(1))
    PARAM = compile(r':([a-z_]+)')

    def url(self, **kw):
        astr = self.url_templ
        for param in self.params:
            astr = astr.replace(':' + param, str(kw[param]))
        return astr

    def to_dict(self):
        return {
            'url_templ': self.url_templ,
            'permission': getattr(self, 'permission', None),
            }

    is_page = True
    is_operation = not is_page


class Operation(Page):
    """Subclass of Page with a ``request_method`` (the HTTP verb)."""

    def __init__(self, name, url_templ, request_method='GET', **kw):
        assert isinstance(request_method, basestring)
        super(Operation, self).__init__(name, url_templ, **kw)
        self.request_method = request_method

    def to_dict(self):
        adict = super(Operation, self).to_dict()
        adict['request_method'] = self.request_method
        return adict

    is_page = False
    is_operation = not is_page


class Burla(object):
    """Collection of pages and operations. Easily turned into a dict for
        JSON output.

        Generates URLs and provides JS code to generate URLs in the client.
        """

    def __init__(self, root='', page_class=Page, op_class=Operation):
        self.map = {}
        self.root = root
        self._page_class = page_class
        self._op_class = op_class

    def _add_page(self, name, **kw):
        assert name not in self.map, 'Already registered: {}'.format(name)
        self.map[name] = self._page_class(name, **kw)

    def _add_op(self, name, **kw):
        assert name not in self.map, 'Already registered: {}'.format(name)
        self.map[name] = self._op_class(name, **kw)

    def url(self, name, **kw):
        """Returns only the generated URL."""
        return self.map[name].url(**kw)

    # def item(self, name, **kw):
    #     """Returns the generated URL and the request_method."""
    #     op = self.map[name]
    #     return {'url': op.url(**kw), 'request_method': op.request_method}

    def add_op(self, name, **kw):
        """Decorator for view handlers that registers an operation with Burla.
            """
        def wrapper(view_handler):
            self._add_op(name, fn=view_handler, **kw)
            return view_handler
        return wrapper

    def add_page(self, name, **kw):
        """Decorator for view handlers that registers a page with Burla."""
        def wrapper(view_handler):
            self._add_page(name, fn=view_handler, **kw)
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
        """Generates documentation from 'section', 'name', 'doc' and
            'permission' attributes of the registered Operation instances,
            in reStructuredText.
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
                    if op.request_method:
                        url_line = op.request_method + ' ' + op.url_templ
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
        """Returns a JS file that contains the operations and pages and
            functions to generate URLs from them.
            """
        return """"use strict";

// Usage:
// var url = burla.page(pageName, urlParams);
// var url = burla.op(operationName, urlParams);

window.burla = {
    root: ROOT,
    pages: PAGES,
    ops: OPERATIONS,

    _find: function (map, name, options) {
        var s = map[name].url_templ;
        if (!s)  throw new Error('burla: No item called "' + name + '".');
        for (var key in options) {
            var placeholder = ':' + key;
            if (s.indexOf(placeholder) == -1) {
                throw new Error('burla: URL template "' + name + '" does not use parameter "' + key + '".');
            }
            var val = options[key];
            if (val == null)  throw new Error('burla: Operation "' + name + '" needs parameter "' + key + '".');
            s = s.replace(placeholder, val);
        }
        return this.root + s;
    },

    page: function (name, options) { return this._find(this.pages, name, options); },
    op: function (name, options) { return this._find(this.ops, name, options); },
}\n""" \
            .replace('PAGES', dumps(
                {o.name: o.to_dict() for o in self.gen_pages()},
                sort_keys=True)) \
            .replace('OPERATIONS', dumps(
                {o.name: o.to_dict() for o in self.gen_ops()},
                sort_keys=True)) \
            .replace('ROOT', dumps(self.root))

DOC_TITLE = _('HTTP API Documentation')
