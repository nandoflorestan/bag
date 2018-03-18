"""Tests the *bag.web.pyramid.locale* module."""

import unittest
from bag.web.pyramid.locale import sorted_countries


class TestLocale(unittest.TestCase):

    def test_sorted_countries(self):
        tups = sorted_countries('pt')
        assert ('ZA', 'África do Sul') in tups
