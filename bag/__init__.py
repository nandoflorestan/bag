#!/usr/bin/env python
# -*- coding: utf-8 -*-
# http://docs.python.org/whatsnew/pep-328.html
from __future__ import absolute_import
from __future__ import print_function   # deletes the print statement
from __future__ import unicode_literals # unicode by default


__version__ = "0.1.3"
__author__   = 'Nando Florestan'
__copyright__ = "Copyright (C) 2010 Nando Florestan"
__license__ = 'BSD'
__url__ = "http://code.google.com/p/bag"
__long_description__ = """Functions and classes for many purposes,
that I use all the time in multiple programs.

The fact that these are just bits and pieces does not prevent them from
having bugs, so they are under version control at
{0}

Hopefully there's something for you here!

Currently, the library requires Python 2.6.x.

Library contents
================

    * csv -- The infamous csv Python module does not support unicode; problem solved.
    * file_id_manager -- Use this to hash your files, store the hashes, and know when you already have some file.
    * file_watcher -- Watches a bunch of files and when one of them is modified, runs a callback. Also useful for reloading Python modules when they are altered.
    * google_translator -- Use the Google translation webservice to translate text.
    * html -- Encode and decode HTML and XML entities.
    * more_codecs -- Got text in some weird encoding that Python doesn't know? OK, use iconv to decode it.
    * percentage_done -- Don't leave your user wondering if your program is hanging; print the percentage of work done every few seconds.
    * sa -- Convenient SQLALchemy initialization, and some types for working with SQLite.
    * text -- Functions for working with unicode strings. 
""".format(__url__)

__doc__ = '''bag library, version {0} — {1}
License: {2}

{3}'''.format(__version__, __copyright__, __license__,
              __long_description__)
