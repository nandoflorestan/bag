# -*- coding: utf-8 -*-

"""The content of this module is for Python 2 only.
See the :py:mod:`bag.spreadsheet.csv` module if you use Python 3.
"""

from __future__ import (absolute_import, division, print_function)
import csv


class CsvWriter(object):
    """A CSV writer that encapsulates a stream and supports encodings."""

    def __init__(self, file, encoding='utf8', delimiter=',',
                 quoting=csv.QUOTE_MINIMAL, lineterminator='\r\n'):
        self._file = file
        self._writer = csv.writer(file, delimiter=str(delimiter),
                                  quoting=quoting,
                                  lineterminator=lineterminator)
        self._enc = encoding

    def close(self):
        """Close the underlying ``file``.

        If it has a ``getvalue()`` method (``StringIO`` objects do),
        the content is returned.
        """
        s = self._file.getvalue() if hasattr(self._file, 'getvalue') \
            else None
        if hasattr(self._file, 'close'):
            self._file.close()
        return s

    def put(self, vals):
        """Write the passed values to the CSV stream.

        Argument: an iterable of unicode or bytes objects. Unicode objects are
        encoded into the output encoding.
        """
        try:
            self._writer.writerow([
                v.encode(self._enc) if isinstance(v, unicode)
                else v for v in vals])
        except UnicodeEncodeError as e:
            print(vals)
            raise e

    @staticmethod
    def file_extension(encoding='utf8'):
        """Return an appropriate file extension such as ".utf8.csv"."""
        return '.{0}.csv'.format(encoding)


def decoding_csv(csv_stream, encoding='utf8'):
    """Wrap a CSV reader in order to yield unicode objects.

    This is a generator that wraps a simple CSV reader in order to give you
    unicode objects in the returned rows. Example::

        f = open('filepath.csv', 'r')
        for vals in decoding_csv(csv.reader(f, delimiter=b','), \
                                 encoding='utf8'):
            print(vals)
        f.close()

    This generator removes the UTF8 BOM if the file contains it.
    """
    # This is the only opportunity I found to remove the UTF8 BOM
    # and still use the csv module.
    row = csv_stream.next()
    if row and row[0].startswith('\xef\xbb\xbf'):
        row[0] = row[0][3:]
        encoding = 'utf8'
    yield([v.decode(encoding) for v in row])
    while True:  # eventually, StopIteration is raised by csv_stream
        row = csv_stream.next()
        yield([v.decode(encoding) for v in row])


class UnicodeDictReader(object):
    """Reads a CSV stream, returning for each row a dictionary.

    The keys are column headers and the values are unicode objects.

    Example::

        csv = UnicodeDictReader(open('myfile', 'r'), delimiter=b',',
                                encoding='iso-8859-1')
        # The constructor has read the first row and memorized the headers,
        # because a 'fieldnames' parameter was not provided.
        for row in csv:
            print(row)  # shows a dictionary
        csv.close()

    It also removes the UTF8 BOM from your data if the file contains it.

    Implementation note: of course the correct way would have been to
    read the file, decode it, then parse it as CSV. That is impossible
    while the Python CSV module does not support unicode objects.

    In Python 3 we don't need this class anymore -- csv supports unicode.
    """

    def __iter__(self):
        return self

    def close(self):
        if hasattr(self.f, 'close'):
            self.f.close()

    def __init__(self, f, fieldnames=None, restkey=None, restval=None,
                 dialect="excel", encoding='utf8', *args, **kwds):
        self.fieldnames = fieldnames   # list of keys for the dict
        self.restkey = restkey         # key to catch long rows
        self.restval = restval         # default value for short rows
        self.encoding = encoding
        self.f = f
        self.reader = csv.reader(f, dialect, *args, **kwds)
        self.dialect = dialect
        self.line_num = 0
        if not fieldnames:  # read fieldnames from the first line now
            try:
                row = self.reader.next()
            except StopIteration:
                pass
            else:
                self.line_num = self.reader.line_num
                if row and row[0].startswith('\xef\xbb\xbf'):
                    row[0] = row[0][3:]
                    self.encoding = 'utf8'
                self.fieldnames = [v.decode(encoding) for v in row]

    def next(self):
        row = self.reader.next()
        while row == []:
            row = self.reader.next()
        self.line_num = self.reader.line_num
        d = dict(zip(self.fieldnames, [v.decode(self.encoding) for v in row]))
        # unlike the basic reader, we prefer not to return blanks,
        # because we will typically wind up with a dict full of
        # None values.
        lf = len(self.fieldnames)
        lr = len(row)
        if lf < lr:
            d[self.restkey] = row[lf:]
        elif lf > lr:
            for key in self.fieldnames[lr:]:
                d[key] = self.restval
        return d
