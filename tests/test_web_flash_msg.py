"""Tests the *bag.web.flash_msg* module."""

import unittest
from bag.web.flash_msg import FlashMessage


class TestFlashMessage(unittest.TestCase):

    def test_plain(self):
        f = FlashMessage(plain='Albatross!!!', kind='error')
        assert f.to_dict() == dict(
            close=True, kind='danger', plain='Albatross!!!', rich=None)
        assert '<div class="alert alert-danger fade in">' \
            '<button type="button" class="close" data-dismiss="alert" ' \
            'aria-label="Close"><span aria-hidden="true">×</span></button>' \
            'Albatross!!!</div>\n' == f.bootstrap_alert

    def test_rich(self):
        f = FlashMessage(rich='<p>Albatross!</p>', kind='danger', close=False)
        assert '<div class="alert alert-danger alert-block fade in">' \
            '<p>Albatross!</p></div>\n' == f.bootstrap_alert
