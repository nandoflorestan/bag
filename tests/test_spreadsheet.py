# -*- coding: utf-8 -*-

"""Tests the *spreadsheet* module."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from unittest import TestCase
from bag.spreadsheet import (raise_if_forbidden_headers, ForbiddenHeaders)


class TestSpreadsheet(TestCase):

    def test_forbidden_headers(self):
        self.assertIsNone(raise_if_forbidden_headers(['number']))
        try:
            raise_if_forbidden_headers(
                ['1', '2', 'number', '4'], forbidden_headers=['number'])
            self.assertTrue(False)
        except ForbiddenHeaders as err:
            self.assertEqual(
                str(err),
                'The spreadsheet contains the forbidden header: number')
            self.assertEqual(err.forbidden_headers[0], 'number')
        try:
            raise_if_forbidden_headers(
                ['1', '2', 'number', '4'], forbidden_headers=['number', '2'])
            self.assertTrue(False)
        except ForbiddenHeaders as err:
            self.assertEqual(
                str(err),
                'The spreadsheet contains the forbidden headers: "number", "2"'
                )
            self.assertEqual(err.forbidden_headers[0], 'number')
            self.assertEqual(err.forbidden_headers[1], '2')
