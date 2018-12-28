"""Easily import a CSV file with headers on the top row.

The most important things here are:

- The :py:func:`csv_with_headers_reader` generator
- The :py:class:`DecodingCsvWithHeaders` class
"""

from codecs import BOM_UTF8, BOM_UTF16
import csv
from . import (
    get_corresponding_variable_names, raise_if_missing_required_headers,
    raise_if_forbidden_headers)


def decoding(stream, encoding='utf8'):
    """Wrap a stream that yields bytes in order to decode it.

    If you have a stream that yields bytes, use this wrapper to decode them
    into str objects. Example::

        f = open('filepath.csv', 'br')
        for line in decode(f, encoding='utf8'):
            print(line)
        f.close()

    This generator removes the UTF8 BOM if the file contains it.
    http://en.wikipedia.org/wiki/Byte_order_mark
    """
    line = stream.readline()

    # Python is buggy, it removes other BOMs but not the UTF8 one.
    if line:
        if line.startswith(BOM_UTF8):
            line = line[len(BOM_UTF8):]
            encoding = 'utf8'
        elif line.startswith(BOM_UTF16):
            encoding = 'utf16'

    yield line.decode(encoding)

    while True:  # eventually, StopIteration is raised by *stream*
        line = stream.readline()
        if not line:
            return
        yield line.decode(encoding)


def setup_reader(stream, required_headers=[], forbidden_headers=[], **k):
    c = csv.reader(stream, **k)

    def readline():
        return c.__next__()

    headers = [h.strip() if isinstance(h, str) else h for h in readline()]
    raise_if_missing_required_headers(headers, required_headers)
    raise_if_forbidden_headers(headers, forbidden_headers)
    vars = get_corresponding_variable_names(headers, required_headers)

    class CsvRow:
        __slots__ = vars

        def __init__(self, vals):
            for i, h in enumerate(vars):
                setattr(self, h, vals[i].strip())

    return c, readline, vars, CsvRow


def csv_with_headers_reader(
    stream, required_headers=[], forbidden_headers=[], **k
):
    """Return an iterator over a CSV reader.

    It uses *stream* with the options passed as keyword arguments.
    The iterator yields objects so you can access the values conveniently.

    In addition, you may pass a sequence of *required_headers*, and if they
    aren't all present, KeyError is raised.

    Let's see an example. Suppose you are reading some CSV file and all you
    know is it contains the columns "Email", "Name" and "Sex", not
    necessarily in that order::

        csv_reader = csv_with_headers_reader(
            open('contacts.csv', mode='r', encoding='utf8'),
            dialect="excel", delimiter=';', required_headers='email')
        for o in csv_reader:
            print(o.name, o.email, o.sex)
    """
    c, readline, headers, CsvRow = setup_reader(
        stream, required_headers, forbidden_headers, **k)
    while True:
        try:
            yield CsvRow(readline())
        except StopIteration:
            return


def decoding_csv_with_headers(bytestream, encoding='utf8', **k):
    """Combines the *decoding* and *csv_with_headers_reader* generators."""
    return csv_with_headers_reader(decoding(bytestream, encoding), **k)


class DecodingCsvWithHeaders:
    """The advantage of using the class instead of the generator is that
    any errors related to the headers happen when the class is
    instantiated, so they can be catched separately.
    """

    def __init__(self, stream, encoding=None, **k):
        if encoding:
            stream = decoding(stream, encoding)
        self.c, self.readline, self.headers, self.CsvRow = setup_reader(
            stream, **k)

    def __iter__(self):
        return self

    def __next__(self):
        return self.CsvRow(self.readline())


def buffered_csv_writing(rows, encoding='utf8', headers=None, buffer_rows=50):
    """Generate CSV lines using a buffer of size *buffer_rows*.

    The values for the first CSV line may be provided as *headers*, and
    the remaining ones as *rows*, which is preferrably another generator.

    For instance, in Pyramid you might have a view like this::

        return Response(content_type='text/csv', app_iter=buffered_csv_writing(
            rows=my_generator, headers=['name', 'email'], buffer_rows=50))
    """
    from io import StringIO
    buf = StringIO()
    writer = csv.writer(buf)
    if headers:
        writer.writerow(headers)
    for i, row in enumerate(rows):
        writer.writerow(row)
        if i % buffer_rows == 0:
            yield buf.getvalue().encode(encoding)
            buf.truncate(0)  # But in Python 3, truncate() does not move
            buf.seek(0)    # the file pointer, so we seek(0) explicitly.
    yield buf.getvalue().encode(encoding)
    buf.close()


def pyramid_download_csv(response, file_title, rows, encoding='utf8', **k):
    response.headers["Content-Type"] = "text/csv"
    response.headers["Content-Disposition"] = content_disposition_value(
        '{}.{}.csv'.format(file_title, encoding))
    response.app_iter = buffered_csv_writing(rows, encoding=encoding, **k)
    return response


def content_disposition_value(file_name):
    """Return the value of a Content-Disposition HTTP header."""
    return 'attachment;filename="{}"'.format(file_name.replace('"', '_'))


"""
Downloading a large CSV file in a web app
=========================================

::

    <mgedmin> I wonder if using app_iter results in less work
    (no need to ''.join() the stringio's internal buffer), or *more* work
    (it ''.joins() and then splits by '\n')
    <mgedmin> a microbenchmark of app_iter=buf versus body=buf.getvalue()
    would be interesting to see
    <nandoflorestan> mgedmin, the second option wouldn't make sense, I think
    <mgedmin> nandoflorestan, I find your faith in Python's stdlib charming
    <mgedmin> /usr/lib/python2.7/StringIO.py: __iter__() returns self,
    next() returns self.readline(),
    self.readline does self.buf += ''.join(self.buflist)
    <mgedmin> maybe cStringIO is more optimized
    <mgedmin> cStringIO in py2.6 doesn't have a buflist, afaics, just a buf
    <mgedmin> so it's just creating many substrings unnecessarily
    <mgedmin> verdict: app_iter creates unnecessary work
    <nandoflorestan> no, the fault isn't with app_iter
    <mgedmin> hm, a proper app-iter based solution for
    dynamically generating gigs of CSV data would be interesting
    <nandoflorestan> well
    <mgedmin> would it be possible to use the stdlib csv module in any way,
    I wonder?
    <nandoflorestan> yes
    <nandoflorestan> it supports file-like objects,
    <mgedmin> but app-iter is pull-based, and csv is push-based
    <nandoflorestan> of which file and StringIO are "subclasses"
    <mgedmin> well, duh, worst case you can treat each set of,
    say, 100 lines, as a separate csv and just let app_iter concatenate those
    <nandoflorestan> The problem you have found is really with
    using StringIO at all
    <nandoflorestan> Just use generators all the way instead
    <nandoflorestan> this make sense?
    <mgedmin> so the question is, I suppose: is it possible to make use of
    the stdlib csv modules knowledge of various CSV dialects and
    CSV escaping rules, when you're rolling your own csv generator?
    * mgedmin isn't solving a real problem, just having thought experiments,BTW
    <mgedmin> mnemoc is the one who needs to generate CSV in a Pyramid view
    and was asking about the best way to do that
    <mgedmin> there were no mentions of the multi-gigabyte data sets
    <nandoflorestan> yes, it is possible, because csv supports a file-like
    interface which must give it one CSV line at a time.
    <nandoflorestan> the csv module does not require that one use StringIO.
    <mgedmin> so?
    <mgedmin> pyramid doesn't have anything like response.write(bunch_of_data)
    <mgedmin> and you can't yield across multiple functions
    <nandoflorestan> 1)that's what app_iter is for
    <nandoflorestan> 2) don't understand
    <mgedmin> I'm curious how you would use csv with app_iter, that's all
    <nandoflorestan> buffer = StringIO()
    <nandoflorestan> writer = CsvWriter(buffer)
    <nandoflorestan> response.headers["Content-Type"] = "text/plain"
    <nandoflorestan> response.headers["Content-Disposition"] = \
        "attachment;filename=" + blahblah
    * mgedmin comes up with this: http://pastie.org/3471360
    <nandoflorestan> mgedmin, exactly. truncate(0)
    <mgedmin> ok
    <mgedmin> I hoped maybe you knew a better solution
    <nandoflorestan> sorry :)
    <mgedmin> actually something like http://pastie.org/3471360 might be
    better -- larger buffers, don't yield after every single line
    <mgedmin> 100 is probably too small but whatever, it's proof of concept
    <nandoflorestan> very nice.


    from io import StringIO
    import csv

    def csv_view(request):  # by mgedmin
        buf = StringIO()
        writer = csv.writer(buf)
        def csvdata():
            for n in range(100000):
                writer.writerow(['fake', 'csv', 'line', str(n)])
                if n % 100 == 99:
                    yield buf.getvalue()
                    buf.truncate(0)
            yield buf.getvalue()
        return Response(content_type='text/csv', app_iter=csvdata)
"""
