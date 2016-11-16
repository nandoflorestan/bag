# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import pkg_resources
# Module version, as defined in PEP-0396.
__version__ = pkg_resources.get_distribution('bag').version
del pkg_resources

_boolean_states = {'1': True, 'yes': True, 'true': True, 'on': True,
                   '0': False, 'no': False, 'false': False, 'off': False}


def asbool(thing):
    """Convert a configuration value to a boolean."""
    if thing is None or isinstance(thing, (bool, int)):
        return thing
    val = _boolean_states.get(thing.lower())
    if val is None:
        raise ValueError('Not a boolean: "%s"' % thing)
    return val


def first(iterable):
    """Return the first object in ``iterable``."""
    for o in iterable:
        return o


def dict_subset(adict, predicate):
    """Return a dict that is a subset of ``adict`` using a filter function.

    The signature of the filter is: ``predicate(key, val) -> bool``
    """
    return {k: v for k, v in adict.items() if predicate(k, v)}
