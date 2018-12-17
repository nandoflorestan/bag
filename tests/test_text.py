"""Tests the *text* module."""

import unittest
from bag.text import to_filename


class TestText(unittest.TestCase):

    def test_to_filename(self):
        self.assertEqual(
            to_filename("Carl Sagan", for_web=True, maxlength=16),
            'Carl-Sagan')
