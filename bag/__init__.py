#!/usr/bin/env python
# -*- coding: utf-8 -*-

__url__ = 'http://code.google.com/p/bag'
__version__ = "0.2.1dev"
__license__ = 'BSD'
__author__ = 'Nando Florestan'
__copyright__ = 'Copyright (C) 2012 Nando Florestan'
__long_description__ = '''
Functions and classes for many purposes,
that I use all the time in multiple programs.

The fact that these are just bits and pieces does not prevent them from
having bugs, so they are under version control at
{0}

Currently, the library requires Python 2.7.x.

Most important library contents
===============================

* **bag.csv** -- The infamous csv Python module does not support unicode;
  problem solved.
* **bag.email_validator** -- The ultimate functions for email validation and
  domain validation, as well as an email address harvester.
* **bag.file_id_manager** -- Use this to hash your files, store the hashes, and
  know when you already have some file.
* **bag.web.transecma** -- Complete solution for
  javascript internationalization. Compatible with jquery templates.
  Includes transecma.js.
* **bag.web.web_deps** -- Ensure your javascript libraries and CSS stylesheets
  appear in the right order, and require them from
  different parts of your code.

If you use the Pyramid web framework
====================================

* **bag.web.pyramid.locale** -- Easily enable and disable locales,
  let users switch languages, and use the browser's languages by default.
* **bag.web.pyramid.plugins_manager** -- Make your Pyramid app extensible
  through plugins.
* **bag.web.pyramid.starter** -- Reusable configurator for
  starting up Pyramid web applications.
* **bag.web.pyramid.genshi** -- Use the Genshi templating language
  with the Pyramid web framework.
* **bag.web.pyramid.kajiki** -- Use the new Kajiki templating language
  with the Pyramid web framework.

Less important library contents
===============================

* **bag.bytes_box** -- Wraps an Image in another object that can
  instantiate it from a number of sources (bytes, files etc.) and then
  copy, resize or write it. The interface is experimental but
  seems to be very convenient.
* **bag.file_watcher** -- Watches a bunch of files and
  when one of them is modified, runs a callback. Also useful for
  reloading Python modules when they are altered.
* **bag.html** -- Encode and decode HTML and XML entities.
* **bag.memoize** -- *Memoize* decorator with a LRU (least recently used)
  cache, which can take a keymaker function as an argument.
* **bag.more_codecs** -- Got text in some weird encoding that
  Python doesn't know? OK, use iconv to decode it.
* **bag.percentage_done** -- Don't leave your user wondering if
  your program is hanging; print the percentage of work done every few seconds.
* **bag.sqlalchemy.context** -- Convenient SQLALchemy initialization, at last.
* **bag.text** -- Functions for working with unicode strings.
'''.format(__url__)

__doc__ = '''bag library, version {0} — {1}
License: {2}

{3}'''.format(__version__, __copyright__, __license__,
              __long_description__)
