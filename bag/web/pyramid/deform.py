#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Functions to set up and more easily use Deform with Pyramid.'''

from __future__ import absolute_import
from __future__ import unicode_literals  # unicode by default
from pkg_resources import resource_filename
import deform as d
from pyramid.i18n import get_localizer
from pyramid.threadlocal import get_current_request
from . import _


def translator(term):
    return get_localizer(get_current_request()).translate(term)


def setup(deform_template_dirs):
    '''Add our deform templates and set deform up for i18n.
    Example:

        setup(['app:fieldtypes/templates', 'deform:templates'])
    '''
    dirs = [resource_filename(*dir.split(':')) for dir in deform_template_dirs]
    d.Form.set_zpt_renderer(dirs, translator=translator)


def get_button(text=_('Submit')):
    '''Gets a string and generates a Deform button while setting its
    `name` attribute and capitalizing the label.
    '''
    return d.Button(title=translator(text).capitalize(),
                    name=filter(unicode.isalpha, text.lower()))


def make_form(form_schema, f_template='form', i_template='mapping_item',
              *args, **kwargs):
    # Adds a csrf token to prevent attacks
    if not 'csrf_token' in kwargs:
        request = get_current_request()
        kwargs['csrf_token'] = request.session.get_csrf_token()
    form = d.Form(form_schema, *args, **kwargs)
    class F(d.widget.FormWidget):
        template = f_template
        item_template = i_template
    form.set_widgets({'':F()})
    return form


# Decorator to verify the csrf_token
def verify_csrf_token(func):
    def wrapper(*a, **kw):
        request = get_current_request()
        token = request.session.get_csrf_token()
        if '__csrf_token__' in request.params and \
            request.params['__csrf_token__'] == token:
            return func(*a, **kw)
        else:
            raise HTTPUnauthorized('CSRF token did not match')
    return wrapper


def monkeypatch_colander():
    '''Alter Colander to fix an issue of versions 0.9.2-0.9.6 where
    All() raises "TypeError: sequence item 0: expected string, list found"
    when child exceptions are used.

    Further, we introduce the more useful asdict2() method.
    '''
    import colander as c
    from colander import interpolate, Invalid

    def __call__(self, node, value):
        msgs = []
        excs = []
        for validator in self.validators:
            try:
                validator(node, value)
            except Invalid, e:
                excs.append(e)
                msgs.append(e.msg)
        if msgs:
            exc = Invalid(node, msgs)
            for e in excs:
                e.children and exc.children.extend(e.children)
            raise exc

    def asdict(self):
        """ Return a dictionary containing a basic
        (non-language-translated) error report for this exception"""
        paths = self.paths()
        errors = {}
        for path in paths:
            keyparts = []
            msgs = []
            for exc in path:
                exc.msg and msgs.extend(exc.messages())
                keyname = exc._keyname()
                keyname and keyparts.append(keyname)
            errors['.'.join(keyparts)] = '; '.join(interpolate(msgs))
        return errors

    def asdict2(self):
        """Also returns a dictionary containing a basic
        (non-language-translated) error report for this exception.

        ``asdict`` returns a dictionary containing fewer items -- the keys
        refer only to the leaves. This method returns a dictionary with
        more items: one key for each node that has an error,
        regardless of whether the node is a leaf or an ancestor.
        Perhaps this way you can place error messages on more places of a form.

        In my application I want to display messages on parents
        as well as leaves... I am not using Deform in this case...
        """
        paths = self.paths()
        errors = []
        for path in paths:  # Each path is a tuple of Invalid instances.
            keyparts = []
            for exc in path:
                keyname = exc._keyname()
                if keyname:
                    keyparts.append(keyname)
                for msg in exc.messages():
                    errors.append(('.'.join(keyparts), msg))
        errors = set(errors)  # Filter out repeats
        adict = {}
        for key, msg in errors:
            if adict.has_key(key):
                adict[key] = adict[key] + '; ' + msg
            else:
                adict[key] = msg
        return adict

    def messages(self):
        """ Return an iterable of error messages for this exception
        using the ``msg`` attribute of this error node.  If the
        ``msg`` attribute is iterable, it is returned.  If it is not
        iterable, a single-element list containing the ``msg`` value
        is returned."""
        if hasattr(self.msg, '__iter__'):
            return self.msg
        elif self.msg:
            return [self.msg]
        else:  # maybe self.msg is None
            return []

    # Colander 0.9.7 corrects the bug, but it still does not contain asdict2().
    from pkg_resources import require, parse_version
    package = require('colander')[0]
    if parse_version(package.version) <= parse_version('0.9.6'):
        print('Monkeypatching Colander to fix its bug.')
        c.All.__call__ = __call__
        c.Invalid.asdict = asdict
        c.Invalid.messages = messages
    # In any case, add asdict2() whose output is more appropriate.
    print('Adding asdict2() to Colander.')
    c.Invalid.asdict2 = asdict2
