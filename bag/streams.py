# -*- coding: utf-8 -*-

"""Functions that use streams (open files)"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


def get_file_size(stream):
    assert stream.seekable(), 'Streams of type {} are not seekable'.format(
        type(stream))
    stream.seek(0, 2)  # Seek to the end of the stream
    size = stream.tell()  # Get the position of EOF
    stream.seek(0)  # Reset the stream position to the beginning
    return size
