#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals  # unicode by default
import random
import os
import re
from datetime import datetime


def parse_iso_date(txt):
    return datetime.strptime(txt[:19], '%Y-%m-%d %H:%M:%S')


def random_string(length, chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ' \
                              'abcdefghijklmnopqrstuvwxyz' \
                              '0123456789'):
    '''Returns a random string of some `length`.'''
    return ''.join((random.choice(chars) for i in xrange(length)))


latin1_map = (('"', '“”'),
              ('-', '\u2013\u2014\u2022'),
              ("'", '\u2018\u2019'),
              ('',  '\ufffd\u2122\u2020'),
              ('...', '\u2026'),
              ('i',   '\u012b'),
              ('ã',   '\u0101'),
              ('r',   '\u0159'),
              ('Z',   '\u017d'),
              ('z',   '\u017e'),
              ('EUR', '\u20ac'),
             )  # chars that ISO-8859-1 does not support

ascii_map = [('a', 'áàâãäå\u0101'),
             ('e', 'éèêẽë'),
             ('i', "íìîĩï"),
             ('o', 'óòôõöø'),
             ('u', "úùûũü"),
             ('A', 'ÁÀÂÃÄÅ'),
             ('E', 'ÉÈÊẼË'),
             ('I', "ÍÌÎĨÏ"),
             ('O', 'ÓÒÔÕÖØ'),
             ('U', "ÚÙÛŨÜ"),
             ('n', "ñ"),
             ('c', "ç"),
             ('N', "Ñ"),
             ('C', "Ç"),
             ('d', "Þ"),
             ('ss', "ß"),
             ('ae', "æ"),
             ('oe', 'œ'),
            ]
ascii_map.extend(latin1_map)


def simplify_chars(txt, encoding='ascii', binary=True, amap=None):
    '''Removes from *txt* (a unicode object) all characters not
    supported by *encoding*, but using a map to "simplify" some
    characters instead of just removing them.
    If *binary* is true, returns a binary string.
    '''
    if amap is None:
        if encoding == 'ascii':
            amap = ascii_map
        elif encoding.replace('-', '') in ('latin1', 'iso88591'):
            amap = latin1_map
    for plain, funny in amap:
        for f in funny:
            txt = txt.replace(f, plain)
    return txt.encode(encoding, 'ignore') if binary else txt


def to_filename(txt, for_web=False, badchars=''):
    '''Massages *txt* until it is a good filename.'''
    illegal = '\\/\t:?"<>|#$%&*[]•' + badchars
    try:
        for c in illegal:
            txt = txt.replace(c, '')
    except UnicodeDecodeError, e:
        if type(txt) == str:
            txt = txt.decode('ascii', 'ignore')
            for c in illegal:
                txt = txt.replace(c, '')
        else:
            raise
    txt = simplify_chars(txt.strip())
    if for_web:
        txt = txt.replace(' ', '-') \
                 .replace('--', '-').replace('--', '-').lower()
    return txt


def find_new_title(dir, filename):
    """If file *filename* exists in directory *dir*, adds or changes the
    end of the file title until a name is found that doesn't yet exist.
    Returns the new path.
    For instance, if file "Image (01).jpg" exists in "somedir",
    returns "somedir/Image (02).jpg".
    """
    rx = re.compile(r"\((\d{1,5})\)$")
    p = os.path.join(dir, filename)
    while os.path.exists(p):
        base = os.path.basename(p)
        (root, ext) = os.path.splitext(base)
        m = rx.search(root)
        if m == None:
            replacement = "(001)"
        else:
            increment = int(m.group(1)) + 1
            replacement = "(%03d)" % increment
            root = root[:m.start(1) - 1]
        f = root + replacement + ext
        p = os.path.join(dir, f)
    return p


""" Removing this function... Just use filter(predicate, txt) instead.
def filter_chars_in(txt, predicate):
    '''Given a string and a function that takes a character and returns
    True or False, returns the filtered string.
    '''
    return ''.join([c for c in txt if predicate(c)])
"""


def keep_digits(txt):
    return txt if txt.isdigit() else \
        filter_chars_in(txt, unicode.isdigit)


def resist_bad_encoding(txt, possible_encodings=('utf8', 'iso-8859-1')):
    """Use this to try to avoid errors from text whose encoding is unknown,
    when erroring out would be worse than possibly displaying garbage.

    Maybe we should use the chardet library instead...
    """
    if not isinstance(txt, str):
        return txt
    best = ''
    for enc in possible_encodings:
        temp = txt.decode(enc, 'ignore')
        if len(temp) > len(best):
            best = temp
    return best


must_be_lowercase = [' ' + s + ' ' for s in \
    'De Do Da Dos Das Em No Na Nos Nas E Para Por Com Sem Sobre '
    'O A Os As Um Uma Uns Umas Num Numa Nuns Numas Dum Duma Duns Dumas '
    'Que À Às Ao Aos Of The And For To With Without In On'.split()]
must_be_uppercase = [' ' + s + ' ' for s in \
    'CD DVD MP3 I II III IV V VII VIII IX X SP RG CPF OAB CREA'
    'CRM SAP PHP LINQ VBA XML'.split()]


def make_title(txt):
    txt = txt.title()
    for word in must_be_lowercase:
        txt = txt.replace(word, word.lower())
    for word in must_be_uppercase:
        txt = txt.replace(word.title(), word)
    return txt