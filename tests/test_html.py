"""Tests the *html* module."""

from unittest import TestCase
from bag.html import decode_entities, encode_xml_char_refs


class TestHtml(TestCase):

    def test_entities(self):
        s = "© áéíóú ãẽõ ôâ à ü"
        t = encode_xml_char_refs(s)
        assert isinstance(t, bytes)
        t = t.decode('utf-8')
        u = decode_entities(t)  # convert it back to the original
        assert s == u, "Conversion to XML char refs and back failed!"
