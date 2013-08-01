# -*- coding: utf-8 -*-

'''Tests the *bag.web.pyramid.locale* module.'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import unittest
from ..web.pyramid.locale import sorted_countries


class TestLocale(unittest.TestCase):
    def test_sorted_countries(self):
        tups = sorted_countries('pt')
        assert ('ZA', 'África do Sul') in tups
