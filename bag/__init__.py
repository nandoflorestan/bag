# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from importlib import import_module
from types import ModuleType
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


def resolve(resource_spec):
    """Return the variable referred to in the ``resource_spec`` string.

    Example resource_spec: ``"my.python.module:some_variable"``.
    """
    if isinstance(resource_spec, ModuleType):  # arg is a python module
        return resource_spec
    module, var = resource_spec.split(':')  # arg is assumed to be a string
    module = import_module(module)
    return getattr(module, var)


def resolve_path(resource_spec):
    """Return a pathlib.Path corresponding to the ``resource_spec`` string.

    Example argument: ``"my.python.module:some/subdirectory"``

    Similar: ``from pyramid.resource import abspath_from_asset_spec``
    """
    from pathlib import Path
    module, var = resource_spec.split(':')  # arg is assumed to be a string
    module = import_module(module)
    return Path(module.__path__[0], var)


def first(iterable):
    """Return the first object in ``iterable``."""
    for o in iterable:
        return o


def dict_subset(adict, predicate):
    """Return a dict that is a subset of ``adict`` using a filter function.

    The signature of the filter is: ``predicate(key, val) -> bool``
    """
    return {k: v for k, v in adict.items() if predicate(k, v)}
