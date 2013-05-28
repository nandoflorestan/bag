# -*- coding: utf-8 -*-

'''Tests the *text* module.'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import unittest
from ..text import to_filename


class TestText(unittest.TestCase):
    def test_to_filename(self):
        self.assertEqual(to_filename("Seeds of Dreams Institute", for_web=True,
            maxlength=16), 'seeds-of-dreams')
