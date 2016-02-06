# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from nine import IS_PYTHON2, nimport, nine, range, str, basestring


def monkeypatch(cls):
    """Decorator. Applied to a function, sets it as a method in a class.
        Applied to a property, sets it on the class, too.
        Example::

            @monkeypatch(MyClass)
            def some_method(self):
                pass
        """
    def _monkeypatch(fn):
        if isinstance(fn, property):
            setattr(cls, fn.fget.__name__, fn)
        else:
            setattr(cls, fn.__name__, fn)
    return _monkeypatch
