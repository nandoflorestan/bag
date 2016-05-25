# -*- coding: utf-8 -*-

"""Tests for ``bag.time``."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import unittest
from datetime import datetime
from bag.time import parse_iso_datetime, naive, now_or_future, utc


class TestTime(unittest.TestCase):
    def test_parse_iso_datetime(self):
        assert datetime(2014, 10, 21) == parse_iso_datetime('2014-10-21')
        assert datetime(2014, 10, 21, 18, 20) == parse_iso_datetime(
            '2014-10-21T18:20')
        assert datetime(2014, 10, 21, 18, 20, 59) == parse_iso_datetime(
            '2014-10-21 18:20:59')
        assert datetime(2014, 10, 21, 18, 20, 59, 777000) == \
            parse_iso_datetime('2014-10-21T18:20:59.777')
        assert datetime(2014, 10, 21, 18, 20, 59, 40000) == \
            parse_iso_datetime('2014-10-21 18:20:59.040Z')

    def test_now_or_future(self):
        now = datetime(2015, 7, 17, tzinfo=utc)
        past = datetime(2015, 7, 16, 23, 59, tzinfo=utc)
        future = datetime(2015, 7, 17, 0, 1, tzinfo=utc)

        assert now is now_or_future(None, now=now)
        assert now is now_or_future(past, now=now)
        assert future == now_or_future(future, now=now)

        # Now let's perform the same tests with naive datetimes.
        past = naive(past)
        future = naive(future)

        assert now is now_or_future(None, now=now)
        assert naive(now) == now_or_future(past, now=now)
        assert future == now_or_future(future, now=now)
