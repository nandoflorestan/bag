# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


class ArgumentError(ValueError):
    def __init__(self, arg, val):
        self.arg = arg
        self.val = val
        val = str(val)
        if len(val) > 43:
            val = val[:40] + '...'
        super(ArgumentError, self).__init__(
            'Argument "{}" does not accept value "{}"'.format(arg, val))
