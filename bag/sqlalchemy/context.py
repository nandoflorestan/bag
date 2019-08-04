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

from functools import wraps
from types import ModuleType

from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base  # , declared_attr
from sqlalchemy.orm import sessionmaker, scoped_session

__all__ = ('SAContext',)


class SAContext:
    """Provide convenient and encapsulated SQLAlchemy initialization."""

    __slots__ = ('base', 'dburi', 'engine', 'Session', '_scoped_session',
                 'use_transaction')

    def __init__(
        self, base=None, base_class=None, metadata=None,
        use_transaction: bool = False, *args, **k
    ):  # noqa
        self.dburi = None
        self.engine = None
        self.Session = None
        self._scoped_session = None
        self.use_transaction = use_transaction
        metadata = metadata or MetaData(naming_convention={
            # https://alembic.readthedocs.org/en/latest/naming.html
            # http://docs.sqlalchemy.org/en/rel_1_0/core/constraints.html#constraint-naming-conventions
            "ix": 'ix_%(table_name)s_%(column_0_label)s',
            "uq": "%(table_name)s_%(column_0_name)s_key",
            "ck": "ck_%(table_name)s_%(column_0_name)s",
            # could be: "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "%(table_name)s_%(column_0_name)s_%(referred_table_name)s_fkey",
            "pk": "%(table_name)s_pkey",
        })
        if base:
            self.base = base
        elif base_class:
            self.base = declarative_base(cls=base_class, metadata=metadata)
        else:
            self.base = declarative_base(name="Base", metadata=metadata)
        if self.metadata.bind:
            self._set_engine(self.metadata.bind)
        if args or k:
            self.create_engine(*args, **k)

    def _set_engine(self, engine):
        self.engine = engine
        self.Session = sessionmaker(bind=engine)
        if self.use_transaction:
            from zope.sqlalchemy import register as _transaction_register
            _transaction_register(self.Session)
        self.dburi = str(engine.url)

    def create_engine(self, dburi: str, **k):
        """Set the engine according to ``dburi``."""
        self._set_engine(create_engine(dburi, **k))
        return self

    def use_memory(self, tables=None, **k):
        """Create an in-memory SQLite engine, and create tables."""
        self.create_engine('sqlite:///:memory:', **k)
        self.create_tables(tables=tables)
        return self

    @property
    def scoped_session(self):
        """Return a (memoized) scoped session.

        This is created only when first used and then stored.
        """
        if not self._scoped_session:
            assert self.Session is not None, \
                'Tried to use the scoped session before the engine was set.'
            self._scoped_session = scoped_session(self.Session)
        return self._scoped_session

    @property
    def metadata(self):  # noqa
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
        """Enclose in a subtransaction a decorated function.

        Your system must use our ``ss`` scoped session and it
        does not need to call ``commit()`` on the session.
        """
        @wraps(fn)
        def wrapper(*a, **kw):
            self.scoped_session.begin(subtransactions=True)
            try:
                fn(*a, **kw)
            except Exception as exc:
                self.scoped_session.rollback()
                raise exc
            else:
                self.scoped_session.commit()
        return wrapper

    def transaction(self, fn):
        """Enclose a decorated function in a transaction.

        Your system must use our ``ss`` scoped session and it
        does not need to call ``commit()`` on the session.
        """
        @wraps(fn)
        def wrapper(*a, **kw):
            try:
                fn(*a, **kw)
            except Exception as exc:
                self.scoped_session.rollback()
                raise exc
            else:
                self.scoped_session.commit()
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
            self.scoped_session.begin(subtransactions=True)
            self.scoped_session.begin(subtransactions=True)
            try:
                fn(*a, **kw)  # I assume fn consumes the inner subtransaction.
            finally:
                self.scoped_session.rollback()  # Revert outer subtransaction
        return wrapper
