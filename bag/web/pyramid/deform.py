#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Functions to set up and more easily use Deform with Pyramid.'''

from __future__ import (absolute_import, division, print_function,
    unicode_literals)
from pkg_resources import resource_filename
import deform as d
from pyramid.httpexceptions import HTTPUnauthorized
from pyramid.i18n import get_localizer
from pyramid.threadlocal import get_current_request
from . import _


def translator(term):
    return get_localizer(get_current_request()).translate(term)


def setup(deform_template_dirs):
    '''Add our deform templates and set deform up for i18n.
    Example:

    .. code-block:: python

        setup(['app:fieldtypes/templates', 'deform:templates'])
    '''
    dirs = tuple([resource_filename(*dir.split(':')) \
        for dir in deform_template_dirs])
    d.Form.set_zpt_renderer(dirs, translator=translator)


def get_button(text=_('Submit')):
    '''Gets a string and generates a Deform button while setting its
    `name` attribute and capitalizing the label.
    '''
    return d.Button(title=translator(text).capitalize(),
                    name=filter(unicode.isalpha, text.lower()))


def verify_csrf(func):
    '''Decorator that checks the CSRF token. TODO: Use and test.'''
    def wrapper(*a, **kw):
        request = get_current_request()
        if request.params.get('_csrf_') == request.session.get_csrf_token():
            return func(*a, **kw)
        else:
            raise HTTPUnauthorized('You do not pass our CSRF protection.')
    return wrapper


def monkeypatch_colander():
    '''Alter Colander 0.9.7 to introduce the more useful asdict2() method.
    '''
    print('Adding asdict2() to Colander.')
    import colander as c
    from colander import interpolate, Invalid

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
            if key in adict:
                adict[key] = adict[key] + '; ' + msg
            else:
                adict[key] = msg
        return adict
    c.Invalid.asdict2 = asdict2
