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
    if thing is None or isinstance(thing, (bool, int)):
        return thing
    val = _boolean_states.get(thing.lower())
    if val is None:
        raise ValueError('Not a boolean: "%s"' % thing)
    return val
