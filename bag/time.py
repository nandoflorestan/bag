"""Functions to make it easier to work with datetimes.

By the way, some ways of constructing a datetime instance::

    datetime.now()    -> datetime(2015, 7, 17, 2, 18, 39, 255470)
    datetime.now(utc) -> datetime(2015, 7, 17, 5, 18, 39, 255497, tzinfo=<UTC>)
    datetime.utcnow() -> datetime(2015, 7, 17, 5, 18, 39, 255543)
"""

import json
from datetime import datetime, timedelta, tzinfo
from decimal import Decimal
from time import sleep
from typing import Optional
from pytz import timezone
utc = timezone('utc')


def now_with_tz() -> datetime:
    """Like datetime.utcnow(), but including tzinfo."""
    return datetime.now(utc)
    return utc.localize(datetime.utcnow())


def naive(dt: datetime) -> datetime:
    """Remove the timezone from a datetime instance."""
    return datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute,
                    dt.second, dt.microsecond)


def parse_iso_datetime(text: str) -> datetime:
    """Convert the given string to a naive (no tzinfo) datetime."""
    text = text.strip()
    if 'T' in text:
        sep = 'T'
    elif ' ' in text:
        sep = ' '
    else:
        sep = ''
    DATE_FMT = "%Y-%m-%d"
    if not sep:
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


def simplify_datetime(val: datetime, granularity: str='minute') -> datetime:
    """Notice this throws away any tzinfo."""
    if granularity == 'hour':
        return datetime(val.year, val.month, val.day, val.hour)
    elif granularity == 'minute':
        return datetime(val.year, val.month, val.day, val.hour, val.minute)
    elif granularity == 'second':
        return datetime(
            val.year, val.month, val.day, val.hour, val.minute, val.second)
    else:
        raise RuntimeError('granularity not implemented: "{}"'.format(
            granularity))


def timed_call(seconds, function, repetitions=-1, *a, **kw):
    """Perform some task every x seconds. Sleep if necessary.

    Do not sleep after the last turn.

    By default, runs forever. To control the number of times
    that *function* should run, pass in a number of *repetitions*.
    Returns immediately if *repetitions* is zero.
    """
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
    """JSON encoder that outputs dates and decimals.

    Example usage::

        DJSONEncoder().encode([datetime.datetime.now()])
        '["2015-01-21T14:42:28"]'
    """

    def default(self, obj):
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(str(obj))
        else:
            return super(DJSONEncoder, self).default(obj)


def dumps(value):
    """Like json.dumps, but using DJSONEncoder."""
    return json.dumps(value, cls=DJSONEncoder)


def djson_renderer_factory(info):
    """Pyramid renderer.

    Install like this::

       config.add_renderer('djson', 'bag.time.djson_renderer_factory')
    """
    def _render(value, system):
        request = system.get('request')
        if request is not None:
            response = request.response
            ct = response.content_type
            if ct == response.default_content_type:
                response.content_type = 'application/json'
        return dumps(value)
    return _render


def now_or_future(
    dt: Optional[datetime], timezone: tzinfo=utc, now: Optional[datetime]=None,
) -> datetime:
    """If given datetime is in the past, default to now.

    Given a datetime, returns it as long as it is not in the past;
    otherwise, returns now.  You may pass the ``timezone`` instance
    for the comparison (defaults to UTC); this is useful if your
    datetime is naive.

    The argument ``now`` should be ignored; it is used only in the unit tests.
    """
    now = now or datetime.now(timezone)
    assert isinstance(now, datetime)

    if not dt:
        return now
    assert isinstance(dt, datetime)

    if dt.tzinfo is None:  # dt is a naive datetime (no timezone)
        now = naive(now)   # comparison only works with another naive datetime

    return now if dt < now else dt
