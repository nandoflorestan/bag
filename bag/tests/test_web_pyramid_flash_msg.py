# -*- coding: utf-8 -*-

'''Tests the *bag.web.pyramid.flash_msg* module.'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import unittest
from bag.web.pyramid.flash_msg import FlashMessage
from pyramid.testing import DummyRequest


class TestFlashMessage(unittest.TestCase):
    def test_plain(self):
        f = FlashMessage(DummyRequest(), 'Albatross!!!', kind='error')
        assert '<div class="alert alert-danger fade in">' \
            '<button type="button" class="close" data-dismiss="alert" ' \
            'aria-label="Close"><span aria-hidden="true">×</span></button>' \
            'Albatross!!!</div>\n' == f.html

    def test_rich(self):
        f = FlashMessage(DummyRequest(), rich='<p>Albatross!!!</p>',
                         kind='danger', close=False)
        assert '<div class="alert alert-danger alert-block fade in">' \
            '<p>Albatross!!!</p></div>\n' == f.html
