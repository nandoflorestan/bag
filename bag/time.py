# -*- coding: utf-8 -*-

'''Functions to make it easier to work with datetimes.'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from datetime import datetime, timedelta
from time import sleep


def simplify_datetime(val, granularity='minute'):
    '''Notice this throws away any tzinfo.'''
    if granularity == 'minute':
        return datetime(val.year, val.month, val.day, val.hour, val.minute)
    if granularity == 'second':
        return datetime(val.year, val.month, val.day, val.hour, val.minute,
            val.second)
    if granularity == 'hour':
        return datetime(val.year, val.month, val.day, val.hour)


def timed_call(seconds, function, repetitions=-1, *a, **kw):
    '''Performs some task every x seconds. Sleeps if necessary.
    Does not sleep after the last turn.

    By default, runs forever. To control the number of times
    that *function* should run, pass in a number of *repetitions*.
    Returns immediately if *repetitions* is zero.
    '''
    period = seconds if isinstance(seconds, timedelta) else \
        timedelta(0, seconds)
    turn = 0
    while True:
        if turn == repetitions:
            return
        if repetitions > -1:
            turn += 1
        started = datetime.utcnow()
        function(*a, **kw)
        took = datetime.utcnow() - started
        if turn != repetitions and took < period:
            sleep((period - took).total_seconds())
