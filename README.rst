bag library
~~~~~~~~~~~

Functions and classes for many purposes,
that I use all the time in multiple programs.

The fact that these are just bits and pieces does not prevent them from
having bugs, so they are under version control at
https://github.com/nandoflorestan/bag

Previously, this library was hosted at
http://code.google.com/p/bag

The library is tested on Python 2.6, 2.7, 3.2 and 3.3.

For documentation on each module, please refer to its own docstrings.

Most important library contents
===============================

* **bag.csv2** -- The infamous csv Python module does not support unicode;
  problem solved.
* **bag.csv3** -- In web apps, uploaded files come as byte streams,
  so we provide a decoding generator. If you'd like the order of the
  CSV columns not to matter, there is a header-based reader. There is
  also a buffered CSV writer for outputting CSV in a web app.
* **bag.email_validator** -- The ultimate functions for email validation and
  domain validation, as well as an email address harvester.
* **bag.file_existence_manager** -- Tools for finding duplicate files
  using hashes.
* **bag.web.transecma** -- Complete solution for
  javascript internationalization. Compatible with jquery templates.
  Includes transecma.js.
* **bag.web.web_deps** -- Ensure your javascript libraries and CSS stylesheets
  appear in the right order, and require them from
  different parts of your code.

If you use the Pyramid web framework
====================================

* **bag.web.pyramid.flash_msg** -- Advanced flash messages scheme for Pyramid.
* **bag.web.pyramid.locale** -- Easily enable and disable locales,
  let users switch languages, and use the browser's languages by default.
* **bag.web.pyramid.plugins_manager** -- Make your Pyramid app extensible
  through plugins.
* **bag.web.pyramid.starter** -- Reusable configurator for
  starting up Pyramid web applications.
* **bag.web.pyramid.genshi** -- Use the Genshi templating language
  with the Pyramid web framework.
* **bag.web.pyramid.kajiki** -- Use the Kajiki templating language
  with the Pyramid web framework.

Less important library contents
===============================

* **bag.bytes_box** -- Wraps an Image in another object that can
  instantiate it from a number of sources (bytes, files etc.) and then
  copy, resize or write it. The interface is experimental but
  seems to be very convenient.
* **bag.check_rst** -- Verifies reStructuredText content for correctness.
* **bag.console** -- Functions for user interaction at the console.
* **bag.file_watcher** -- Watches a bunch of files and
  when one of them is modified, runs a callback. Also useful for
  reloading Python modules when they are altered.
* **bag.log** -- Convenient logging initialization.
* **bag.html** -- Encode and decode HTML and XML entities.
* **bag.memoize** -- *Memoize* decorator with a LRU (least recently used)
  cache, which can take a keymaker function as an argument.
* **bag.more_codecs** -- Got text in some weird encoding that
  Python doesn't know? OK, use iconv to decode it.
* **bag.percentage_done** -- Don't leave your user wondering if
  your program is hanging; print the percentage of work done every few seconds.
* **bag.sqlalchemy.context** -- Convenient SQLALchemy initialization, at last.
* **bag.text** -- Functions for working with unicode strings.
