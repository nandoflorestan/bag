# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import pkg_resources
# Module version, as defined in PEP-0396.
__version__ = pkg_resources.get_distribution('bag').version
del pkg_resources


def first(iterable):
    """Return the first object in ``iterable``."""
    for o in iterable:
        return o


def dict_subset(adict, predicate):
    """Return a dict that is a subset of ``adict`` using a filter function.

    The signature of the filter is: ``predicate(key, val) -> bool``
    """
    return {k: v for k, v in adict.items() if predicate(k, v)}
