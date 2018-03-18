"""Deal with HTML markup."""

import re
from html.entities import name2codepoint


def encode_xml_char_refs(s):
    # http://mail.python.org/pipermail/python-list/2007-January/424262.html
    return s.encode('ascii', 'xmlcharrefreplace')


def _substitute_entity(match):
    ent = match.group(3)
    if match.group(1) == "#":        # decode by number
        if match.group(2) == '':     # number is decimal
            return chr(int(ent))
        elif match.group(2) == 'x':  # number is hex
            return chr(int('0x' + ent, 16))
    else:
        cp = name2codepoint.get(ent)  # decode by name
        if cp:
            return chr(cp)
        else:
            return match.group()


def decode_entities(txt):
    return entity_re.subn(_substitute_entity, txt)[0]
entity_re = re.compile(r'&(#?)(x?)(\w+);', flags=re.IGNORECASE)


def html_to_unicode(html):
    html = decode_entities(html).replace('\r\n', ' ') \
        .replace('\r', ' ').replace('\n', ' ').replace('\t', ' ') \
        .replace('<br />', '\n').replace('<br>', '\n').strip()
    regex = re.compile(r' {2,999}')
    return regex.sub(' ', html)
