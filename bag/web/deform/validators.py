#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Useful generic validators for colander.'''

from __future__ import (absolute_import, division, print_function,
    unicode_literals)
import colander as c
try:
    from ..web.pyramid import _
except ImportError:
    _ = str  # and i18n is disabled.


@c.deferred
def from_now_on(node, kw):
    return c.Range(min=kw['now'],
        # min_err=_('${val} is in the past. Current time is ${min}'))
        min_err=_('Cannot be in the past. Current time is ${min}'))
