#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals  # unicode by default
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import (Table, Column, ForeignKey, Sequence, desc,
    UniqueConstraint, and_, or_, MetaData, create_engine,
    __version__ as sa_version)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import (mapper, sessionmaker, scoped_session, validates,
    relationship, backref, deferred, eagerload, object_session)  # , synonym
# http://www.postgresql.org/docs/9.1/static/datatype-numeric.html
from sqlalchemy.types import (Unicode, UnicodeText, Date, DateTime, Boolean,
                    SmallInteger, Integer, BigInteger, DECIMAL, LargeBinary)
from types import ModuleType
from .tricks import pk, now_column, CreatedChanged, CASC


class SAContext(object):
    '''Convenient SQLALchemy initialization.

    Usage:

    .. code-block:: python

        from bag.sqlalchemy.context import *
        # The above single statement imports most if not all of
        # what you need to define a model and use it.

        sa = SAContext()  # you can provide create_engine's args here
        # Now define your model with sa.metadata and sa.base

        # Add a working engine:
        sa.create_engine('sqlite:///db.sqlite3', echo=False)
        # or...
        sa.use_memory()  # This one immediately creates the tables.

        # Now use it:
        sa.drop_tables().create_tables()
        session = sa.Session()
        # Use that session...
        session.commit()

        # You can also create a copy of sa, bound to another engine:
        sa2 = sa.clone('sqlite://')
    '''
    __slots__ = ('base', 'dburi', 'engine', 'Session', 'session_extensions')

    def __init__(self, base=None, metadata=None, session_extensions=None,
                 *args, **k):
        self.dburi = None
        self.engine = None
        self.Session = None
        self.session_extensions = session_extensions
        if base:
            self.base = base
        else:
            self.base = declarative_base(metadata=metadata)
        if self.metadata.bind:
            self._set_engine(self.metadata.bind)
        if args or k:
            self.create_engine(*args, **k)

    def _set_engine(self, engine):
        self.engine = engine
        self.Session = sessionmaker(bind=engine,
                                    extension=self.session_extensions)
        self.dburi = unicode(engine.url)

    @property
    def metadata(self):
        return self.base.metadata

    def create_engine(self, dburi, **k):
        self._set_engine(create_engine(dburi, **k))
        return self

    def use_memory(self, tables=None, **k):
        self.create_engine('sqlite:///:memory:', **k)
        self.create_tables(tables=tables)
        return self

    def drop_tables(self, tables=None):
        self.metadata.drop_all(tables=tables, bind=self.engine)
        return self

    def create_tables(self, tables=None):
        self.metadata.create_all(tables=tables, bind=self.engine)
        return self

    def tables_in(self, context):
        '''*context* may be a dictionary or a module.

        Returns a list containing the tables in the passed *context*::

            tables = sa.tables_in(globals())
        '''
        tables = []
        if isinstance(context, ModuleType):  # context is a python module
            context = context.__dict__
        for val in context.values():
            if hasattr(val, '__base__') and val.__base__ is self.base:
                tables.append(val.__table__)
            elif isinstance(val, Table) and val.metadata is self.metadata:
                tables.append(val)
        return tables

    def clone(self, **k):
        from copy import copy
        o = copy(self)
        if k:
            o.create_engine(**k)
        return o


"""
# TYPES FOR SQLITE
# ================
import sqlalchemy.types as types
class AutoDate(types.TypeDecorator):
    '''A SQLAlchemy DateTime type that converts strings to datetime
    when storing. Prevents TypeError("SQLite Date, Time, and DateTime types
    only accept Python datetime objects as input.")
    '''
    impl = types.DateTime

    def process_bind_param(self, value, dialect):
        if isinstance(value, basestring):
            if value == '':
                return None
            parts = value.split('.')
            dt = datetime.strptime(parts[0], "%Y-%m-%d %H:%M:%S")
            if len(parts) > 1:
                dt.replace(microsecond=int(parts[1]))
            return dt
        else:
            return value


class Integer(types.TypeDecorator):
    impl = types.Integer

    def process_bind_param(self, value, dialect):
        '''Make sure an int is persisted. Otherwise, SQLite might persist
        things such as empty strings...
        '''
        # return None if not value else int(value)
        return None if value is None or value == '' else int(value)


class Numeric(types.TypeDecorator):
    impl = types.Numeric

    def process_bind_param(self, value, dialect):
        '''When you are feeding a CSV file to a SQLite database, you
        want empty strings to be automatically converted to None,
        for a Decimal column...
        '''
        return None if value == '' else value

del types
"""


__doc__ = SAContext.__doc__
