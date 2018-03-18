"""Reorders the translations inside a .po file.

This script was written because transifex is messy and when you pull
translations from transifex, the order of the strings completely changes and
when you do a ``git diff`` you cannot make sense of the alterations.
It is even hard to see whether any translations have been lost.
But if you always reorder the .po after pulling from transifex, then
the diff will be readable and the version history will make sense.
"""

from argh import ArghParser, arg  # easy_install argh
from pathlib import Path
from polib import pofile  # easy_install -UZ polib


@arg('path', help='.po file to be sorted, or a directory containing .po files')
@arg('-e', '--encoding', default='utf-8', help='.po file encoding')
def reorder_po(path, encoding='utf-8'):
    p = Path(path)
    if p.is_dir():
        for path in p.glob('**.po'):
            _reorder_one(str(path), encoding=encoding)
    else:
        _reorder_one(str(path), encoding=encoding)


def _reorder_one(path, encoding='utf-8'):
    po = pofile(path, encoding=encoding)
    po.sort()
    po.save(path)


def command():
    # http://argh.readthedocs.org/en/latest/
    parser = ArghParser(description=__doc__)
    parser.set_default_command(reorder_po)
    parser.dispatch()

if __name__ == '__main__':
    command()
