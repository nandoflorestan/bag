# -*- coding: utf-8 -*-

'''Tests for ``bag.time``.'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import unittest
from datetime import datetime
from datetime import timedelta
from bag.time import parse_iso_datetime
from bag.time import now_or_future
from bag.time import simplify_datetime


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
        assert simplify_datetime(now_or_future(None)) == \
               simplify_datetime(datetime.now())
        assert simplify_datetime(now_or_future(datetime.now() +
               timedelta(days=-1))) == simplify_datetime(datetime.now())
        assert simplify_datetime(now_or_future(datetime.now() +
               timedelta(days=1))) == simplify_datetime(datetime.now() +
               timedelta(days=1))

