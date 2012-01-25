#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals  # unicode by default
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import Table, Column, Sequence, ForeignKey, desc, or_, \
                       MetaData, create_engine, __version__ as sa_version
from sqlalchemy.types import Unicode, UnicodeText, DateTime, Boolean, \
                             Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, deferred, synonym, relation, eagerload, \
                           mapper, sessionmaker, scoped_session
try:
    from sqlalchemy.types import LargeBinary
except ImportError as e:
    from sqlalchemy.types import Binary as LargeBinary
try:
    from sqlalchemy.exc import IntegrityError
except ImportError:
    from sqlalchemy.exceptions import IntegrityError

if sa_version.split(".") < ["0", "5", "7"]:
    raise ImportError('Version 0.5.7 or later of SQLAlchemy required; '
                      'you are using {0}.'.format(sa_version))
del sa_version


CASC = 'all, delete-orphan'


class SAContext(object):
    '''Convenient SQLALchemy initialization.

    Usage:

        from bag.sa import *
        # The above single statement imports most if not all of
        # what you need to define a model and use it.
        sa = SAContext('sqlite:///db.sqlite3', echo=False, convert_unicode=True)
        # Define your model with sa.metadata, sa.base, sa.engine etc.
        # Then use it:
        sa.drop_tables()
        sa.create_tables()
        session = sa.Session()
        # Use that session...
        session.commit()
        # You can also create a copy of sa, bound to another engine:
        sa2 = sa.clone_with_engine('sqlite://')
    '''
    __slots__ = ('metadata', 'base', 'dburi', 'engine', 'Session')

    def __init__(self, *args, **k):
        self.metadata = MetaData()
        self.base = declarative_base(metadata=self.metadata)
        if args or k:
            self.create_engine(*args, **k)

    def create_engine(self, dburi, echo=False, convert_unicode=True):
        self.dburi = dburi
        self.engine = create_engine \
            (dburi, echo=echo, convert_unicode=convert_unicode)
        self.Session = sessionmaker(bind=self.engine)

    def drop_tables(self, tables=None):
        self.metadata.drop_all(tables=tables, bind=self.engine)

    def create_tables(self, tables=None):
        self.metadata.create_all(tables=tables, bind=self.engine)

    def tables_in(self, adict):
        '''Returns a list containing the tables in the context *adict*.

        Usage:  tables = sa.tables_in(globals())
        '''
        tables = []
        for val in adict.values():
            if hasattr(val, '__base__') and val.__base__ == self.base:
                tables.append(val.__table__)
            elif isinstance(val, Table):
                tables.append(val)
        return tables

    def clone_with_engine(self, *args, **k):
        from copy import copy
        o = copy(self, *args, **k)
        return o


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
