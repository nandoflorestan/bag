# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


def encode_xml_char_refs(s):
    # http://mail.python.org/pipermail/python-list/2007-January/424262.html
    return s.encode('ascii', 'xmlcharrefreplace')


from htmlentitydefs import name2codepoint
import re

''' Old version

def _replace_entity(m):
     s = m.group(1)
     if s[0] == '#':
         s = s[1:]
         try:
             if s[0] in 'xX':
                 c = int(s[1:], 16)
             else:
                 c = int(s)
             return unichr(c)
         except ValueError:
             return m.group(0)
     else:
         try:
             return unichr(name2codepoint[s])
         except (ValueError, KeyError):
             return m.group(0)

_entity_re = re.compile(r"&(#?[xX]?(?:[0-9a-fA-F]+|\w{1,8}));")
def decode_xml_char_refs(s):
     return _entity_re.sub(_replace_entity, s)

'''


def _substitute_entity(match):
    ent = match.group(3)
    if match.group(1) == "#":        # decode by number
        if match.group(2) == '':     # number is decimal
            return unichr(int(ent))
        elif match.group(2) == 'x':  # number is hex
            return unichr(int('0x' + ent, 16))
    else:
        cp = name2codepoint.get(ent)  # decode by name
        if cp:
            return unichr(cp)
        else:
            return match.group()


def decode_entities(txt):
    return entity_re.subn(_substitute_entity, txt)[0]
entity_re = re.compile(r'&(#?)(x?)(\w+);', flags=re.IGNORECASE)


def test_entities():
    # TODO Convert into a proper unit test
    s = "© áéíóú ãẽõ ôâ à ü"
    t = encode_xml_char_refs(s)
    u = decode_entities(t)
    assert s == u, "Conversion to XML char refs and back failed!"


def html_to_unicode(html):
    html = decode_entities(html).replace('\r\n', ' ') \
        .replace('\r', ' ').replace('\n', ' ').replace('\t', ' ') \
        .replace('<br />', '\n').replace('<br>', '\n').strip()
    regex = re.compile(r' {2,999}')
    return regex.sub(' ', html)
