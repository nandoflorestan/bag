===========
bag library
===========

Functions and classes for many purposes,
that I use all the time in multiple programs.

I use SQLAlchemy and Pyramid a lot.

The library is hosted at
https://github.com/nandoflorestan/bag

Previously, this library was hosted at
http://code.google.com/p/bag

The library is tested on Python 2.6, 2.7, 3.3, 3.4 and 3.5.

For documentation on each module, please refer to its own docstrings.

This version was published with `releaser <https://pypi.python.org/pypi/releaser>`_.


Most important library contents
===============================

- `bag.csv2 <https://github.com/nandoflorestan/bag/blob/master/bag/csv2.py>`_
  -- The infamous csv Python module does not support unicode; problem solved.
- `bag.spreadsheet <https://github.com/nandoflorestan/bag/blob/master/bag/spreadsheet>`_
  -- Import CSV and Excel spreadsheets based on headers on the first row.
  There is also a buffered CSV writer for outputting CSV in a web app.
- `bag.email_validator <https://github.com/nandoflorestan/bag/blob/master/bag/email_validator.py>`_
  -- The ultimate functions for email validation and
  domain validation, as well as an email address harvester.
- `bag.web.burla <https://github.com/nandoflorestan/bag/blob/master/bag/web/burla.py>`_ -- Powerful URL generation independent of web frameworks, working in Python and in the client (Javascript) too. Also provided is `Pyramid integration <https://github.com/nandoflorestan/bag/blob/master/bag/web/pyramid/burla.py>`_.
- `bag.web.transecma <https://github.com/nandoflorestan/bag/blob/master/bag/web/transecma.py>`_
  -- Complete solution for javascript internationalization. Compatible with
  jquery templates. Includes
  `transecma.js <https://github.com/nandoflorestan/bag/blob/master/bag/web/transecma.js>`_.
- `bag.web.web_deps <https://github.com/nandoflorestan/bag/blob/master/bag/web/web_deps.py>`_
  -- Ensure your javascript libraries and CSS stylesheets appear in the right
  order, and require them from different parts of your code.


If you use the Pyramid web framework
====================================

- `bag.web.pyramid.angular_csrf <https://github.com/nandoflorestan/bag/blob/master/bag/web/pyramid/angular_csrf.py>`_
  -- Make Pyramid play ball with AngularJS to achieve CSRF protection.
- `bag.web.pyramid.flash_msg <https://github.com/nandoflorestan/bag/blob/master/bag/web/pyramid/flash_msg.py>`_
  -- Advanced flash messages scheme for Pyramid.
- `bag.web.pyramid.locale <https://github.com/nandoflorestan/bag/blob/master/bag/web/pyramid/locale.py>`_
  -- Easily enable and disable locales, let users switch languages,
  and use the browser's languages by default.
- `bag.web.pyramid.nav <https://github.com/nandoflorestan/bag/blob/master/bag/web/pyramid/nav.py>`_
  -- Simple web menu system (navigation).
- `bag.web.pyramid.plugins_manager <https://github.com/nandoflorestan/bag/blob/master/bag/web/pyramid/plugins_manager.py>`_
  -- Make your Pyramid app extensible through plugins.
- `bag.web.pyramid.resources <https://github.com/nandoflorestan/bag/blob/master/bag/web/pyramid/resources.py>`_
- `bag.web.exceptions <https://github.com/nandoflorestan/bag/blob/master/bag/web/exceptions.py>`_
  -- The Problem exception is good for throwing from a service layer, then
  caught in the view layer to be shown to the user.
  -- Functions and base resources for context objects (Pyramid traversal).
- `bag.web.pyramid.routes <https://github.com/nandoflorestan/bag/blob/master/bag/web/pyramid/routes.py>`_
  -- Make Pyramid routes and the route_path() function available to JS in the client.
- `bag.web.pyramid.genshi <https://github.com/nandoflorestan/bag/blob/master/bag/web/pyramid/genshi.py>`_
  -- Use the Genshi templating language with the Pyramid web framework.
  Though perhaps one might prefer
  `Kajiki <https://pypi.python.org/pypi/Kajiki>`_.


If you use SQLAlchemy
=====================

- `bag.sqlalchemy.context <https://github.com/nandoflorestan/bag/blob/master/bag/sqlalchemy/context.py>`_
  -- Convenient SQLAlchemy initialization, at last.
- `bag.sqlalchemy.mediovaigel <https://github.com/nandoflorestan/bag/blob/master/bag/sqlalchemy/mediovaigel.py>`_ -- Complete solution for database fixtures using SQLAlchemy.
- `bag.sqlalchemy.testing <https://github.com/nandoflorestan/bag/blob/master/bag/sqlalchemy/testing.py>`_
  -- Fake objects for unit testing code that uses SQLAlchemy.
- `bag.sqlalchemy.tricks <https://github.com/nandoflorestan/bag/blob/master/bag/sqlalchemy/tricks.py>`_
  -- Various SQLAlchemy gimmicks, including a great base model class.


Commands
========

- `delete_old_branches <https://github.com/nandoflorestan/bag/blob/master/bag/git/delete_old_branches.py>`_
  -- Deletes git branches that have already been merged onto the current branch.
  Optionally, filter the branches by age (in days).
- `reorder_po <https://github.com/nandoflorestan/bag/blob/master/bag/reorder_po.py>`_
  -- Reorders .po files (usually after transifex messes up the order of the
  translations in them) so the diff is always readable.


Less important library contents
===============================

- **bag.bytes_box** -- Wraps an Image in another object that can
  instantiate it from a number of sources (bytes, files etc.) and then
  copy, resize or write it. The interface is experimental but
  seems to be very convenient.
- `bag.check_rst <https://github.com/nandoflorestan/bag/blob/master/bag/check_rst.py>`_
  -- Verifies reStructuredText content for correctness.
- `bag.console <https://github.com/nandoflorestan/bag/blob/master/bag/console.py>`_
  -- Functions for user interaction at the console.
- `bag.corrupt_image <https://github.com/nandoflorestan/bag/blob/master/bag/corrupt_image.py>`_
  -- Read image files and do something if they are corrupt.
- `bag.file_existence_manager <https://github.com/nandoflorestan/bag/blob/master/bag/file_existence_manager.py>`_
  -- Tools for finding duplicate files using hashes.
- **bag.file_watcher** -- Watches a bunch of files and
  when one of them is modified, runs a callback. Also useful for
  reloading Python modules when they are altered.
- `bag.log <https://github.com/nandoflorestan/bag/blob/master/bag/log.py>`_
  -- Convenient logging initialization.
- **bag.html** -- Encode and decode HTML and XML entities.
- `bag.memoize <https://github.com/nandoflorestan/bag/blob/master/bag/memoize.py>`_
  -- *Memoize* decorator with a LRU (least recently used)
  cache, which can take a keymaker function as an argument.
- **bag.more_codecs** -- Got text in some weird encoding that
  Python doesn't know? OK, use iconv to decode it.
- `bag.show_progress <https://github.com/nandoflorestan/bag/blob/master/bag/show_progress.py>`_
  -- Don't leave your user wondering if your program is hanging;
  print the progress every few seconds.
- `bag.streams <https://github.com/nandoflorestan/bag/blob/master/bag/streams.py>`_
  -- Functions that use streams (open files).
- `bag.text <https://github.com/nandoflorestan/bag/blob/master/bag/text.py>`_
  -- Functions for working with unicode strings.
- `bag.time <https://github.com/nandoflorestan/bag/blob/master/bag/time.py>`_
  -- Functions to make it easier to work with datetimes.
  Includes a JSON encoder that supports time, datetime and Decimal.
