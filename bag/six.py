#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Helps with compatibility between Python 2 and 3.
This module imports everything from six (the library), so you can
chain-import everything like this::

    from bag.six import *  # for Python 2 and 3 compatibility

Among other things, on Py3 this gets you the "unicode" word back, so you can
leave code like ``isinstance(something, unicode)`` alone.

But note ``isinstance(something, string_types)`` may be better because it
checks for *basestring* in Python 2 and *str* in Python 3.

Be sure to check out our ``@compat23`` class decorator.
'''

from __future__ import (absolute_import, division, print_function,
    unicode_literals)
from six import *  # http://packages.python.org/six/

PY2 = sys.version_info[0] == 2

try:
    unicode
except NameError:
    unicode = basestring = str


def compat23(cls):
    '''Class decorator that changes the __repr__() method so, under Python 2,
    it returns a binary string.

    Under Python 3, __unicode__() is copied into __str__().
    '''
    if PY2:
        if hasattr(cls, '__repr__'):
            cls.__repr_old = cls.__repr__

            def wrapper(self):
                return self.__repr_old().encode('ascii', 'replace')
            cls.__repr__ = wrapper
    else:
        if hasattr(cls, '__unicode__'):
            cls.__str__ = cls.__unicode__
    return cls
