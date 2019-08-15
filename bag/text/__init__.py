"""Functions to manipulate strings."""

import codecs
import random
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Callable, Generator, List, Optional, Tuple  # noqa


def parse_iso_date(txt: str) -> datetime:
    """Parse a datetime in ISO format."""
    return datetime.strptime(txt[:19], '%Y-%m-%d %H:%M:%S')


def shorten(txt: str, length: int=10, ellipsis: str='…') -> str:
    """Truncate ``txt``, adding ``ellipsis`` to end, with total ``length``."""
    if len(txt) > length:
        return txt[:length - len(ellipsis)] + ellipsis
    else:
        return txt


def shorten_proper(
    name: str, length: int=11, ellipsis: str='…', min: int=None
) -> str:
    """Shorten a proper name for displaying."""
    min = min or int(length / 2.0)
    words = name.split(' ')
    output = []  # type: List[str]
    ln = -1
    while words:
        word = words.pop(0)
        ln += len(word) + 1
        if ln > length:
            break
        output.append(word)
    short = ' '.join(output)
    return short if short and len(short) >= min \
        else shorten(name, length=length, ellipsis=ellipsis)


def uncommafy(txt: str, sep: str=',') -> Generator[str, None, None]:
    """Generate the elements of a comma-separated string.

    Takes a comma-delimited string and returns a generator of
    stripped strings. No empty string is yielded.
    """
    for item in txt.split(sep):
        item = item.strip()
        if item:
            yield item


def random_string(
    length: int,
    chars: str='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
) -> str:
    """Return a random string of some `length`."""
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

ascii_map = (('a', 'áàâãäå\u0101'),
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
             ) + latin1_map


def simplify_chars(txt, encoding='ascii', byts=False, amap=None):
    """Remove from ``txt`` all characters not supported by ``encoding``...

    but using a map to "simplify" some characters instead of
    just removing them.

    If ``byts`` is true, return a bytestring.
    """
    if not amap:
        if encoding == 'ascii':
            amap = ascii_map
        elif encoding.replace('-', '') in ('latin1', 'iso88591'):
            amap = latin1_map
    for plain, funny in amap:
        for f in funny:
            txt = txt.replace(f, plain)
    return txt.encode(encoding, 'ignore') if byts else txt


def to_filename(
    txt: str, for_web: bool=False, badchars: str='', maxlength: int=0,
    encoding='latin1',
) -> str:
    """Massage ``txt`` until it is a good filename."""
    txt = simplify_chars(txt, encoding=encoding).strip()
    illegal = '\\/\t:?\'"<>|#$%&*[]•' + badchars
    for c in illegal:
        txt = txt.replace(c, '')
    if maxlength:
        txt = txt[:maxlength].strip()
    if for_web:
        txt = txt.replace(' ', '-') \
                 .replace('--', '-').replace('--', '-')
    return txt


def slugify(
    txt: str, exists: Callable[[str], bool]=lambda x: False, badchars: str='',
    maxlength: int=16, chars: str='abcdefghijklmnopqrstuvwxyz23456789',
    min_suffix_length: int=1, max_suffix_length: int=4,
) -> str:
    """Return a slug that does not yet exist, based on ``txt``.

    You may provide ``exists``, a callback that takes a generated slug and
    checks the database to see if it already exists.

    Each attempt generates a longer suffix in order to keep the number of
    attempts at a minimum.
    """
    slug1 = slug = to_filename(txt, for_web=True, badchars=badchars,
                               maxlength=maxlength - max_suffix_length - 1)
    while exists(slug):
        rnd = random_string(min_suffix_length, chars=chars)
        slug = slug1 + '-' + rnd
        if min_suffix_length != max_suffix_length:
            min_suffix_length += 1
    return slug


def find_new_title(dir: str, filename: str) -> str:
    """Return a path that does not exist yet, in ``dir``.

    If ``filename`` exists in ``dir``, adds or changes the
    end of the file title until a name is found that doesn't yet exist.

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


def keep_digits(txt: str) -> str:
    """Discard from ``txt`` all non-numeric characters."""
    return ''.join(filter(str.isdigit, txt))


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


def capitalize(txt: str) -> str:
    """Trim, then turn only the first character into upper case.

    This function can be used as a colander preparer.
    """
    if txt is None or (
            not isinstance(txt, str) and repr(txt) == '<colander.null>'):
        return txt
    txt = str(txt).strip()
    if txt == '':
        return txt
    val = txt[0].upper()
    if len(txt) > 1:
        val += txt[1:]
    return val


def strip_preparer(value):
    """Colander preparer that trims whitespace around argument *value*."""
    if isinstance(value, str):
        return value.strip()
    else:
        return value


def strip_lower_preparer(value):
    """Colander preparer that trims whitespace and converts to lowercase."""
    if isinstance(value, str):
        return value.strip().lower()
    else:
        return value


def content_of(paths, encoding='utf-8', sep='\n'):
    """Read, join and return the contents of ``paths``.

    Makes it easy to read one or many files.
    """
    if isinstance(paths, Path):
        paths = [str(paths)]
    elif isinstance(paths, str):
        paths = [paths]
    content = []
    for path in paths:
        with codecs.open(path, encoding=encoding) as stream:
            content.append(stream.read())
    return sep.join(content)


def pluralize(singular: Optional[str]) -> str:
    """Return plural form of given lowercase singular word (English only).

    Based on ActiveState recipe http://code.activestate.com/recipes/413172/

    >>> pluralize('')
    ''
    >>> pluralize('goose')
    'geese'
    >>> pluralize('dolly')
    'dollies'
    >>> pluralize('genius')
    'genii'
    >>> pluralize('jones')
    'joneses'
    >>> pluralize('pass')
    'passes'
    >>> pluralize('zero')
    'zeros'
    >>> pluralize('casino')
    'casinos'
    >>> pluralize('hero')
    'heroes'
    >>> pluralize('church')
    'churches'
    >>> pluralize('x')
    'xs'
    >>> pluralize('car')
    'cars'

    """
    ABERRANT_PLURAL_MAP = {
        'appendix': 'appendices',
        'barracks': 'barracks',
        'cactus': 'cacti',
        'child': 'children',
        'criterion': 'criteria',
        'deer': 'deer',
        'echo': 'echoes',
        'elf': 'elves',
        'embargo': 'embargoes',
        'focus': 'foci',
        'fungus': 'fungi',
        'goose': 'geese',
        'hero': 'heroes',
        'hoof': 'hooves',
        'index': 'indices',
        'knife': 'knives',
        'leaf': 'leaves',
        'life': 'lives',
        'man': 'men',
        'mouse': 'mice',
        'nucleus': 'nuclei',
        'person': 'people',
        'phenomenon': 'phenomena',
        'potato': 'potatoes',
        'self': 'selves',
        'syllabus': 'syllabi',
        'tomato': 'tomatoes',
        'torpedo': 'torpedoes',
        'veto': 'vetoes',
        'woman': 'women',
    }

    VOWELS = frozenset('aeiou')

    if not singular:
        return ''
    plural = ABERRANT_PLURAL_MAP.get(singular)
    if plural:
        return plural
    root = singular
    try:
        if singular[-1] == 'y' and singular[-2] not in VOWELS:
            root = singular[:-1]
            suffix = 'ies'
        elif singular[-1] == 's':
            if singular[-2] in VOWELS:
                if singular[-3:] == 'ius':
                    root = singular[:-2]
                    suffix = 'i'
                else:
                    root = singular[:-1]
                    suffix = 'ses'
            else:
                suffix = 'es'
        elif singular[-2:] in ('ch', 'sh'):
            suffix = 'es'
        else:
            suffix = 's'
    except IndexError:
        suffix = 's'
    plural = root + suffix
    return plural
