#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Functions to make it easier to work with datetimes.'''

from __future__ import (absolute_import, division, print_function,
    unicode_literals)
from datetime import datetime


def simplify_datetime(val, granularity='minute'):
    '''Notice this throws away any tzinfo.'''
    if granularity == 'minute':
        return datetime(val.year, val.month, val.day, val.hour, val.minute)
    if granularity == 'second':
        return datetime(val.year, val.month, val.day, val.hour, val.minute,
            val.second)
    if granularity == 'hour':
        return datetime(val.year, val.month, val.day, val.hour)
