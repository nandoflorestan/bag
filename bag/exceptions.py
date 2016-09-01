# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


class ArgumentError(ValueError):
    """Use this exception to complain that ``arg`` doesn't accept ``val``."""

    def __init__(self, arg, val):
        self.arg = arg
        self.val = val
        val = str(val)
        if len(val) > 43:
            val = val[:40] + '...'
        super(ArgumentError, self).__init__(
            'Argument "{0}" does not accept value "{1}"'.format(arg, val))
