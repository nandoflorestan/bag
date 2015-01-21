# -*- coding: utf-8 -*-

'''Functions to make it easier to work with datetimes.'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import json
from datetime import datetime, timedelta
from decimal import Decimal
from time import sleep
from pytz import timezone
utc = timezone('utc')


def now_with_tz():
    return utc.localize(datetime.utcnow())


def naive(dt):
    return datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute,
                    dt.second, dt.microsecond)


def parse_iso_datetime(text):
    '''Converts the given string to a naive (no tzinfo) datetime.'''
    text = text.strip()
    if 'T' in text:
        sep = 'T'
    elif ' ' in text:
        sep = ' '
    else:
        sep = None
    DATE_FMT = "%Y-%m-%d"
    if sep is None:
        return datetime.strptime(text, DATE_FMT)
    elif len(text) == 16:
        return datetime.strptime(text, DATE_FMT + sep + '%H:%M')
    elif len(text) == 19:
        return datetime.strptime(text, DATE_FMT + sep + '%H:%M:%S')
    else:
        TIME_FMT = "%H:%M:%S.%f"
        suffix = 'Z' if text.endswith('Z') else ''
        fmt = DATE_FMT + sep + TIME_FMT + suffix
        return datetime.strptime(text, fmt)


def simplify_datetime(val, granularity='minute'):
    '''Notice this throws away any tzinfo.'''
    if granularity == 'hour':
        return datetime(val.year, val.month, val.day, val.hour)
    if granularity == 'minute':
        return datetime(val.year, val.month, val.day, val.hour, val.minute)
    if granularity == 'second':
        return datetime(
            val.year, val.month, val.day, val.hour, val.minute, val.second)


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


class DJSONEncoder(json.JSONEncoder):
    '''Example usage::

            DJSONEncoder().encode([datetime.datetime.now()])
            '["2015-01-21T14:42:28"]'
        '''

    def default(self, obj):
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(str(obj))
        else:
            return super(DJSONEncoder, self).default(obj)


def dumps(value):
    return json.dumps(value, cls=DJSONEncoder)


def djson_renderer_factory(info):
    '''Pyramid renderer. Install like this::

       config.add_renderer('djson', 'bag.time.djson_renderer_factory')
    '''
    def _render(value, system):
        request = system.get('request')
        if request is not None:
            response = request.response
            ct = response.content_type
            if ct == response.default_content_type:
                response.content_type = 'application/json'
        return dumps(value)
    return _render
