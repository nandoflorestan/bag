#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv


class CsvWriter(object):
    '''A CSV writer that encapsulates a stream and supports encodings.'''
    def __init__(self, file, encoding='utf8', delimiter=',',
                 quoting=csv.QUOTE_MINIMAL, lineterminator='\r\n'):
        self._file = file
        self._writer = csv.writer(file, delimiter=str(delimiter),
                                  quoting=quoting,
                                  lineterminator=lineterminator)
        self._enc = encoding

    def close(self):
        '''Closes the underlying "file". If it has a getvalue() method
        (StringIO objects do), the content is returned.
        '''
        s = self._file.getvalue() if hasattr(self._file, 'getvalue') \
            else None
        if hasattr(self._file, 'close'):
            self._file.close()
        return s

    def put(self, vals):
        '''Writes the passed values to the CSV stream.
        Argument: an iterable of unicode or bytes objects. Unicode objects are
        encoded into the output encoding.
        '''
        try:
            self._writer.writerow([v.encode(self._enc) \
                if isinstance(v, unicode) else v for v in vals])
        except UnicodeEncodeError as e:
            print(vals)
            raise e

    @staticmethod
    def file_extension(encoding='utf8'):
        '''Returns an appropriate file extension such as ".utf8.csv".'''
        return '.{0}.csv'.format(encoding)


def decoding_csv(csv_stream, encoding='utf8'):
    '''
    Generator that wraps a simple CSV reader in order to give you
    unicode objects in the returned rows. Example:

    f = open('filepath.csv', 'r')
    for vals in decoding_csv(csv.reader(f, delimiter=b','), \
                             encoding='utf8'):
        print(vals)
    f.close()

    This generator removes the UTF8 BOM if the file contains it.
    '''
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
    '''Reads a CSV stream, returning for each row a dictionary where
    the keys are column headers and the values are unicode objects.

    Example:

        csv = UnicodeDictReader(open('myfile', 'r'), delimiter=b',',
                                encoding='iso-8859-1')
        # The constructor has read the first row and memorized the headers,
        # because a 'fieldnames' parameter was not provided.
        for row in csv:
            print(row) # shows a dictionary
        csv.close()

    It also removes the UTF8 BOM from your data if the file contains it.

    Implementation note: of course the correct way would have been to
    read the file, decode it, then parse it as CSV. That is impossible
    while the Python CSV module does not support unicode objects.
    '''
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


'''
Downloading a large CSV file in a web app
=========================================

::

    <mgedmin> I wonder if using app_iter results in less work (no need to ''.join() the stringio's internal buffer), or *more* work (it ''.joins() and then splits by '\n')
    <mgedmin> a microbenchmark of app_iter=buf versus body=buf.getvalue() would be interesting to see
    <nandoflorestan> mgedmin, the second option wouldn't make sense, I think
    <mgedmin> nandoflorestan, I find your faith in Python's stdlib charming
    <mgedmin> /usr/lib/python2.7/StringIO.py: __iter__() returns self, next() returns self.readline(), self.readline does self.buf += ''.join(self.buflist)
    <mgedmin> maybe cStringIO is more optimized
    <mgedmin> cStringIO in py2.6 doesn't have a buflist, afaics, just a buf
    <mgedmin> so it's just creating many substrings unnecessarily
    <mgedmin> verdict: app_iter creates unnecessary work
    <nandoflorestan> no, the fault isn't with app_iter
    <mgedmin> hm, a proper app-iter based solution for dynamically generating gigs of CSV data would be interesting
    <nandoflorestan> well
    <mgedmin> would it be possible to use the stdlib csv module in any way, I wonder?
    <nandoflorestan> yes
    <nandoflorestan> it supports file-like objects,
    <mgedmin> but app-iter is pull-based, and csv is push-based
    <nandoflorestan> of which file and StringIO are "subclasses"
    <mgedmin> well, duh, worst case you can treat each set of, say, 100 lines, as a separate csv and just let app_iter concatenate those
    <nandoflorestan> The problem you have found is really with using StringIO at all
    <nandoflorestan> Just use generators all the way instead
    <nandoflorestan> this make sense?
    <mgedmin> so the question is, I suppose: is it possible to make use of the stdlib csv modules knowledge of various CSV dialects and CSV escaping rules, when you're rolling your own csv generator?
    * mgedmin isn't solving a real problem, just having thought experiments, BTW
    <mgedmin> mnemoc is the one who needs to generate CSV in a Pyramid view and was asking about the best way to do that
    <mgedmin> there were no mentions of the multi-gigabyte data sets
    <nandoflorestan> yes, it is possible, because csv supports a file-like interface which must give it one CSV line at a time.
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
    <nandoflorestan> response.headers["Content-Disposition"] = "attachment;filename=" + blahblah
    * mgedmin comes up with this: http://pastie.org/3471360
    <nandoflorestan> mgedmin, exactly. truncate(0)
    <mgedmin> ok
    <mgedmin> I hoped maybe you knew a better solution
    <nandoflorestan> sorry :)
    <mgedmin> actually something like http://pastie.org/3471360 might be better -- larger buffers, don't yield after every single line
    <mgedmin> 100 is probably too small but whatever, it's proof of concept
    <nandoflorestan> very nice.


    from cStringIO import StringIO
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
'''
