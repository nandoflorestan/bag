===========
bag library
===========

**bag** contains code for many purposes, which I find myself reusing in
multiple programs -- so this code must be version-controlled.
I use SQLAlchemy and Pyramid a lot.

**Documentation** is at http://docs.nando.audio/bag/latest/

The code is at
https://github.com/nandoflorestan/bag
where you can do your bug reports and pull requests.

- bag 0.8.0 is the last version that supported Python 2.6.
- bag 0.9.0 is the last version that supported Python 2.7.
- bag 1.3.0 is the last version that supported Python 3.4.
- bag 2.0 requires Python 3.5's "typing" module for gradual typing.
- bag 2.1.0 is the last version that supported Python 3.5.

This version of **bag** was published with
`releaser <https://pypi.python.org/pypi/releaser>`_.


Most important library contents
===============================

- `bag.spreadsheet <http://docs.nando.audio/bag/latest/api/bag.spreadsheet.html>`_
  -- Import CSV and Excel spreadsheets based on headers on the first row.
  There is also a buffered CSV writer for outputting CSV in a web app.
- `bag.email_validator <http://docs.nando.audio/bag/latest/api/bag.email_validator.html>`_
  -- The ultimate functions for email validation and
  domain validation, as well as an email address harvester.
- `bag.pathlib_complement <http://docs.nando.audio/bag/latest/api/bag.pathlib_complement.html>`_
  -- A Path subclass that does what pathlib doesn't do.
- `bag.subcommand <http://docs.nando.audio/bag/latest/api/bag.subcommand.html>`_
  -- Use argh to dispatch to subcommands with their command-line arguments.
- `bag.web.burla <http://docs.nando.audio/bag/latest/api/bag.web.burla.html>`_
  -- Powerful URL generation independent of web frameworks, working in Python and in the client (Javascript) too. Also provided is `Pyramid integration for it <https://github.com/nandoflorestan/bag/blob/master/bag/web/pyramid/burla.py>`_.
- `bag.web.flash_msg <http://docs.nando.audio/bag/latest/api/bag.web.flash_msg.html>`_
  -- Advanced flash messages for any web framework. Also provided is `Pyramid integration <https://github.com/nandoflorestan/bag/blob/master/bag/web/pyramid/flash_msg.py>`_.
- `bag.web.transecma <http://docs.nando.audio/bag/latest/api/bag.web.transecma.html>`_
  -- Complete solution for javascript internationalization. Compatible with
  jquery templates. Includes
  `transecma.js <https://github.com/nandoflorestan/bag/blob/master/bag/web/transecma.js>`_.


If you use the Pyramid web framework
====================================

- `bag.web.pyramid.angular_csrf <http://docs.nando.audio/bag/latest/api/bag.web.pyramid.angular_csrf.html>`_
  -- Make Pyramid play ball with AngularJS to achieve CSRF protection.
- `bag.web.pyramid.locale <http://docs.nando.audio/bag/latest/api/bag.web.pyramid.locale.html>`_
  -- Easily enable and disable locales, let users switch languages,
  and use the browser's languages by default.
- `bag.web.pyramid.nav <http://docs.nando.audio/bag/latest/api/bag.web.pyramid.nav.html>`_
  -- Simple web menu system (navigation).
- `bag.web.pyramid.plugins_manager <http://docs.nando.audio/bag/latest/api/bag.web.pyramid.plugins_manager.html>`_
  -- Make your Pyramid app extensible through plugins.
- `bag.web.pyramid.resources <http://docs.nando.audio/bag/latest/api/bag.web.pyramid.resources.html>`_
- `bag.web.exceptions <http://docs.nando.audio/bag/latest/api/bag.web.exceptions.html>`_
  -- The Problem exception is good for throwing from a service layer, then
  caught in the view layer to be shown to the user.
  -- Functions and base resources for context objects (Pyramid traversal).
- `bag.web.pyramid.routes <http://docs.nando.audio/bag/latest/api/bag.web.pyramid.routes.html>`_
  -- Make Pyramid routes and the route_path() function available to JS in the client.
- `bag.web.pyramid.genshi <http://docs.nando.audio/bag/latest/api/bag.web.pyramid.genshi.html>`_
  -- Use the Genshi templating language with the Pyramid web framework.
  Though perhaps one might prefer
  `Kajiki <https://pypi.python.org/pypi/Kajiki>`_.


If you use SQLAlchemy
=====================

- `bag.sqlalchemy.context <http://docs.nando.audio/bag/latest/api/bag.sqlalchemy.context.html>`_
  -- Convenient SQLAlchemy initialization, at last.
- `bag.sqlalchemy.mediovaigel <http://docs.nando.audio/bag/latest/api/bag.sqlalchemy.mediovaigel.html>`_ -- Complete solution for database fixtures using SQLAlchemy.
- `bag.sqlalchemy.testing <http://docs.nando.audio/bag/latest/api/bag.sqlalchemy.testing.html>`_
  -- Fake objects for unit testing code that uses SQLAlchemy. Tests will run
  much faster because no database is accessed.
- `bag.sqlalchemy.tricks <http://docs.nando.audio/bag/latest/api/bag.sqlalchemy.tricks.html>`_
  -- Various SQLAlchemy gimmicks, including a great base model class.


Commands
========

- `delete_old_branches <http://docs.nando.audio/bag/latest/api/bag.git.delete_old_branches.html>`_
  -- Deletes git branches that have already been merged onto the current branch.
  Optionally, filter the branches by age (in days).
- `reorder_po <http://docs.nando.audio/bag/latest/api/bag.reorder_po.html>`_
  -- Reorders .po files (usually after transifex messes up the order of the
  translations in them) so the diff is always readable.


Less important library contents
===============================

- `bag.check_rst <http://docs.nando.audio/bag/latest/api/bag.check_rst.html>`_
  -- Verifies reStructuredText content for correctness.
- `bag.console <http://docs.nando.audio/bag/latest/api/bag.console.html>`_
  -- Functions for user interaction at the console.
- `bag.corrupt_image <http://docs.nando.audio/bag/latest/api/bag.corrupt_image.html>`_
  -- Read image files and do something if they are corrupt.
- `bag.file_existence_manager <http://docs.nando.audio/bag/latest/api/bag.file_existence_manager.html>`_
  -- Tools for finding duplicate files using hashes.
- `bag.log <http://docs.nando.audio/bag/latest/api/bag.log.html>`_
  -- Convenient logging initialization.
- **bag.html** -- Encode and decode HTML and XML entities.
- `bag.memoize <http://docs.nando.audio/bag/latest/api/bag.memoize.html>`_
  -- *Memoize* decorator with a LRU (least recently used)
  cache, which can take a keymaker function as an argument.
- **bag.more_codecs** -- Got text in some weird encoding that
  Python doesn't know? OK, use iconv to decode it.
- `bag.show_progress <http://docs.nando.audio/bag/latest/api/bag.show_progress.html>`_
  -- Don't leave your user wondering if your program is hanging;
  print the progress every few seconds.
- `bag.streams <http://docs.nando.audio/bag/latest/api/bag.streams.html>`_
  -- Functions that use streams (open files).
- `bag.text <http://docs.nando.audio/bag/latest/api/bag.text.html>`_
  -- Functions for working with unicode strings.
- `bag.text.words <http://docs.nando.audio/bag/latest/api/bag.text.words.html>`_
  -- Contains lists of nouns and adjectives and can generate a random combination words
  -- good for generating funny test data.
- `bag.time <http://docs.nando.audio/bag/latest/api/bag.time.html>`_
  -- Functions to make it easier to work with datetimes.
  Includes a JSON encoder that supports time, datetime and Decimal.


Compiling the documentation
===========================

Install ``make``, activate your virtualenv, and then::

    pip install sphinx sphinx-autodoc-typehints
    ./build_sphinx_documentation.sh
