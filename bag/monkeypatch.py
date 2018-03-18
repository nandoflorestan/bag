# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from nine import IS_PYTHON2, nimport, nine, range, str, basestring


def monkeypatch(cls, name=None):
    """Decorator. Applied to a function, sets it as a method in a class.

    This can be used above a property, too. Example::

        @monkeypatch(MyClass)
        def some_method(self):
            pass
    """
    def _monkeypatch(fn):
        nam = name or (
            fn.fget.__name__ if isinstance(fn, property) else fn.__name__)
        setattr(cls, nam, fn)
    return _monkeypatch
