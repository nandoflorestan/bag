# -*- coding: utf-8 -*-

"""Convenient, encapsulated SQLALchemy initialization.

Usage::

    from bag.sqlalchemy.context import SAContext

    sa = SAContext()  # you can provide create_engine's args here
    # Now define your models with sa.metadata and sa.base

    # At runtime:
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
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from functools import wraps
from sqlalchemy import Table, create_engine
from sqlalchemy.ext.declarative import declarative_base  # , declared_attr
from sqlalchemy.orm import sessionmaker, scoped_session
from types import ModuleType
from nine import str

__all__ = ('SAContext',)


class SAContext(object):
    """Provide convenient and encapsulated SQLAlchemy initialization."""

    __slots__ = ('base', 'dburi', 'engine', 'Session', '_scoped_session',
                 'session_extensions')

    def __init__(self, base=None, base_class=None, metadata=None,
                 session_extensions=None, zope_transaction=False, *args, **k):
        self.dburi = None
        self.engine = None
        self.Session = None
        self._scoped_session = None
        if base:
            self.base = base
        elif base_class:
            self.base = declarative_base(cls=base_class, metadata=metadata)
        else:
            self.base = declarative_base(metadata=metadata)
        self.session_extensions = session_extensions or []
        if zope_transaction:
            from zope.sqlalchemy import ZopeTransactionExtension
            self.session_extensions.append(ZopeTransactionExtension())
        if self.metadata.bind:
            self._set_engine(self.metadata.bind)
        if args or k:
            self.create_engine(*args, **k)

    def _set_engine(self, engine):
        self.engine = engine
        self.Session = sessionmaker(bind=engine,
                                    extension=self.session_extensions)
        self.dburi = str(engine.url)

    def create_engine(self, dburi, **k):
        self._set_engine(create_engine(dburi, **k))
        return self

    def use_memory(self, tables=None, **k):
        self.create_engine('sqlite:///:memory:', **k)
        self.create_tables(tables=tables)
        return self

    @property
    def ss(self):
        """Return a (memoized) scoped session.

        This is created only when first used and then stored.
        """
        if not self._scoped_session:
            assert self.Session is not None, \
                'Tried to use the scoped session before the engine was set.'
            self._scoped_session = scoped_session(self.Session)
        return self._scoped_session

    @property
    def metadata(self):
        return self.base.metadata

    def drop_tables(self, tables=None):
        """Drop tables."""
        self.metadata.drop_all(tables=tables, bind=self.engine)
        return self

    def create_tables(self, tables=None):
        """Create tables."""
        self.metadata.create_all(tables=tables, bind=self.engine)
        return self

    def tables_in(self, context):
        """Return a list containing the tables in the passed *context*.

        ``context`` may be a dictionary or a module::

            tables = sa.tables_in(globals())
        """
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
        """Copy this object. If keyword args, create another engine."""
        from copy import copy
        o = copy(self)
        if k:
            o.create_engine(**k)
        return o

    def subtransaction(self, fn):
        """Decorator that encloses the decorated function in a subtransaction.

        Your system must use our ``ss`` scoped session and it
        does not need to call ``commit()`` on the session.
        """
        @wraps(fn)
        def wrapper(*a, **kw):
            self.ss.begin(subtransactions=True)
            try:
                fn(*a, **kw)
            except:
                self.ss.rollback()
                raise
            else:
                self.ss.commit()
        return wrapper

    def transaction(self, fn):
        """Decorator that encloses the decorated function in a transaction.

        Your system must use our ``ss`` scoped session and it
        does not need to call ``commit()`` on the session.
        """
        @wraps(fn)
        def wrapper(*a, **kw):
            try:
                fn(*a, **kw)
            except:
                self.ss.rollback()
                raise
            else:
                self.ss.commit()
        return wrapper

    def transient(self, fn):
        """Decorator. Create a subtransaction which is always rewinded.

        It is recommended that you apply this
        decorator to each of your integrated tests; then you only need to
        create the tables once, instead of once per test,
        because nothing ever gets persisted. This makes tests run faster.
        """
        @wraps(fn)
        def wrapper(*a, **kw):
            self.ss.begin(subtransactions=True)
            self.ss.begin(subtransactions=True)
            try:
                fn(*a, **kw)  # I assume fn consumes the inner subtransaction.
            finally:
                self.ss.rollback()  # Revert the outer subtransaction.
        return wrapper


'''
# TYPES FOR SQLITE
# ================
import sqlalchemy.types as types
class AutoDate(types.TypeDecorator):
    """A SQLAlchemy DateTime type that converts strings to datetime
    when storing. Prevents TypeError("SQLite Date, Time, and DateTime types
    only accept Python datetime objects as input.")
    """
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
        """Make sure an int is persisted. Otherwise, SQLite might persist
        things such as empty strings...
        """
        # return None if not value else int(value)
        return None if value is None or value == '' else int(value)


class Numeric(types.TypeDecorator):
    impl = types.Numeric

    def process_bind_param(self, value, dialect):
        """When you are feeding a CSV file to a SQLite database, you
        want empty strings to be automatically converted to None,
        for a Decimal column...
        """
        return None if value == '' else value

del types
'''
