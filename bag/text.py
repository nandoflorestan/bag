# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import codecs
import random
import os
import re
from datetime import datetime
from nine import basestring, str, range


def parse_iso_date(txt):
    return datetime.strptime(txt[:19], '%Y-%m-%d %H:%M:%S')


def shorten(txt, length=10, ellipsis='…'):
    '''Truncate *txt*, adding *ellipsis* to the end, with total *length*.'''
    if len(txt) > length:
        return txt[:length - len(ellipsis)] + ellipsis
    else:
        return txt


def shorten_proper(name, length=11, ellipsis='…', min=None):
    '''Shortens a proper name for displaying.'''
    min = min or length / 2.0
    words = name.split(' ')
    output = []
    l = -1
    while words:
        word = words.pop(0)
        l += len(word) + 1
        if l > length:
            break
        output.append(word)
    output = ' '.join(output)
    return output if output and len(output) >= min \
        else shorten(name, length=length, ellipsis=ellipsis)


def uncommafy(txt, sep=','):
    '''Takes a comma-delimited string and returns a generator of
    stripped strings. No empty string is yielded.
    '''
    for item in txt.split(sep):
        item = item.strip()
        if item:
            yield item


def random_string(length, chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                                'abcdefghijklmnopqrstuvwxyz'
                                '0123456789'):
    '''Returns a random string of some `length`.'''
    return ''.join((random.choice(chars) for i in range(length)))


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


def simplify_chars(txt, encoding='ascii', byts=False, amap=None):
    '''Removes from *txt* (a unicode object) all characters not
    supported by *encoding*, but using a map to "simplify" some
    characters instead of just removing them.
    If *byts* is true, returns a bytestring.
    '''
    if amap is None:
        if encoding == 'ascii':
            amap = ascii_map
        elif encoding.replace('-', '') in ('latin1', 'iso88591'):
            amap = latin1_map
    for plain, funny in amap:
        for f in funny:
            txt = txt.replace(f, plain)
    return txt.encode(encoding, 'ignore') if byts else txt


def to_filename(txt, for_web=False, badchars='', maxlength=0):
    '''Massages *txt* until it is a good filename.'''
    illegal = '\\/\t:?\'"<>|#$%&*[]•' + badchars
    for c in illegal:
        txt = txt.replace(c, '')
    txt = simplify_chars(txt).strip()
    if maxlength:
        txt = txt[:maxlength].strip()
    if for_web:
        txt = txt.replace(' ', '-') \
                 .replace('--', '-').replace('--', '-').lower()
    return txt


def slugify(txt, exists=lambda x: False, badchars='', maxlength=16,
            chars='abcdefghijklmnopqrstuvwxyz23456789',
            min_suffix_length=1, max_suffix_length=4):
    '''Returns a slug that does not yet exist, based on ``txt``.

    You may provide ``exists``, a callback that takes a generated slug and
    checks the database to see if it already exists.

    Each attempt generates a longer suffix in order to keep the number of
    attempts at a minimum.
    '''
    slug1 = slug = to_filename(txt, for_web=True, badchars=badchars,
                               maxlength=maxlength - max_suffix_length - 1)
    while exists(slug):
        rnd = random_string(min_suffix_length, chars=chars)
        slug = slug1 + '-' + rnd
        if min_suffix_length != max_suffix_length:
            min_suffix_length += 1
    return slug


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
        if m is None:
            replacement = "(001)"
        else:
            increment = int(m.group(1)) + 1
            replacement = "(%03d)" % increment
            root = root[:m.start(1) - 1]
        f = root + replacement + ext
        p = os.path.join(dir, f)
    return p


def keep_digits(txt):
    return filter(str.isdigit, txt)


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


must_be_lowercase = [' ' + s + ' ' for s in
    'De Do Da Dos Das Em No Na Nos Nas E Para Por Com Sem Sobre '
    'O A Os As Um Uma Uns Umas Num Numa Nuns Numas Dum Duma Duns Dumas '
    'Que À Às Ao Aos Of The And For To With Without In On'.split()]
must_be_uppercase = [' ' + s + ' ' for s in
    'CD DVD MP3 I II III IV V VII VIII IX X SP RG CPF OAB CREA'
    'CRM SAP PHP LINQ VBA XML'.split()]


def make_title(txt):
    txt = txt.title()
    for word in must_be_lowercase:
        txt = txt.replace(word, word.lower())
    for word in must_be_uppercase:
        txt = txt.replace(word.title(), word)
    return txt


def content_of(paths, encoding='utf-8', sep='\n'):
    if isinstance(paths, basestring):
        paths = [paths]
    content = []
    for path in paths:
        with codecs.open(path, encoding=encoding) as stream:
            content.append(stream.read())
    return sep.join(content)
