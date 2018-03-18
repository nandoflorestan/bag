"""Fake objects for unit testing code that uses SQLAlchemy.

**Problem:** SQLAlchemy is the main thing making our automated tests slow.
In larger systems, hitting the database (even if SQLite in memory)
leads to multiple-minute test suite runs, making TDD (Test First) impossible.

Mocking SQLAlchemy is impossibly hard to keep doing in numerous tests
because the SQLAlchemy API is made of many objects and methods
(session, query, filter, order_by, all, first, one etc.).
It is bad to need to change the mocks every time you change an
implementation detail!

Is there really no easy way to unit-test code that uses SQLAlchemy?

Come on, we are programmers! We can do this!

**Solution 1:** Create a fake session which can be populated with entities
in the Arrange phase of the unit test, and then provides these entities
to the code being tested. :py:class:`FakeSessionByType` is a fake that
does this -- it only pays attention to the model class being queried
and ignores all filters and order_bys and whatever else.

This solution was moderately successful, but what is annoying in it is that,
unlike the real session, it does not populate entities with their IDs
when it is flushed -- neither does it take care of foreign keys.

**Solution 2:** The ambitious :py:class:`FakeSession` is an implementation
of the session that also stores entities in memory but tries to behave
like a real session and actually interpret queries and filters and orders
and so on and so forth. Currently it only works for very simple queries,
but with your help it could become the perfect solution in the future.

**Solution 3:** As of 2016-05, I am sidestepping this as I try to implement
Robert C. Martin's **Clean Architecture** in Python, which forbids I/O
in the center layers of the system. The only place in the system that can
import and use the session is the
`Repository <https://gist.github.com/uris77/4711015>`_,
which is dependency-injected into the service layer. This means the
repository will contain one function per operation or query --
thus it must be easy to mock. We'll see.
"""

import operator
from bag import first
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.sql.elements import BindParameter, ColumnElement


class FakeNoAutoFlush:

    def __enter__(self, *a):
        pass

    def __exit__(self, *a):
        pass


class BaseFakeSession:
    """Base class for fake SQLAlchemy sessions. Look at the subclasses."""

    no_autoflush = FakeNoAutoFlush()

    def __init__(self):
        self.flush_called = 0
        self.new = []
        self.deleted = []

    def add(self, entity):
        self.new.append(entity)

    def delete(self, entity):
        self.deleted.append(entity)

    def flush(self):
        self.flush_called += 1

    def query(self, *typs):
        return self.query_cls(self, typs)


class BaseFakeQuery:
    """Base class for Query objects. Look at the subclasses."""

    def __init__(self, sas, typs):
        self.sas = sas
        self.typs = typs

    def _clone(self):
        """Each method called on query returns a new query which must not
        affect the original.
        """
        clone = self.__class__(self.sas, list(self.typs))
        # Subclasses should then update any other info in the clone
        return clone

    def all(self):
        return list(self)

    def first(self):
        """Return a matching entity, or None."""
        return first(self)

    def one(self):
        """Ensure there is only one result and returns i, or raise."""
        alist = self.all()
        if not alist:
            raise NoResultFound("No row was found for one()")
        elif len(alist) > 1:
            raise MultipleResultsFound("Multiple rows were found for one()")
        else:
            return alist[0]

    def get(self, id):
        # TODO What if someone is using "pk" instead of "id"?
        # TODO What about composite primary keys?
        for entity in self:
            if entity.id == id:
                return entity
        else:
            return None

    def count(self):
        return len(self.all())


class FakeSessionByType(BaseFakeSession):
    """Mock session that returns query results based on the model type.

    This mock session can be configured to return the results you want
    based on the model type being queried.
    """

    def __init__(self, *a, query_cls=None, **kw):
        super().__init__(*a, **kw)
        self.query_cls = query_cls or FakeQueryByType
        self._results = {}

    def add_query_results(self, typs, results):
        if isinstance(typs, tuple):
            pass
        elif isinstance(typs, (list, set, frozenset)):
            typs = tuple(typs)
        else:
            typs = (typs,)  # Put model class in a tuple
        self._results[typs] = results


class FakeQueryByType(BaseFakeQuery):

    def __iter__(self):
        return self.sas._results[self.typs].__iter__()

    def filter(self, *a, **kw):
        return self

    join = filter_by = order_by = filter  # args are ignored


class FakeSession(BaseFakeSession):
    """SQLALchemy session mock intended for use in quick unit tests.
    Because even SQLite in memory is far too slow for real unit tests.

    Uses lists as an in-memory "database" which can be inspected at the
    end of a unit test.  Tries to behave like autoflush mode.
    You can actually make queries on this session, but only simple
    queries work right now.

    Use it like a real SQLAlchemy session::

        sas = FakeSession()
        user = User(name="Johann Gambolputty")
        sas.add(user)
        assert user in sas.db[User]
        sas.add_all((Address(address="221b Baker Street"),
                     Address(address="185 North Gower Street")))
        sas.flush()  # optional because next line does autoflush
        q = sas.query(User)  # returns a FakeQuery instance
        q1 = q.filter_by(name="Johann Gambolputty")  # a new FakeQuery
        assert user == q1.first()
        assert user == q1.one()
        assert [user] == q1.all()
        assert [] == sas.query(User).filter_by(
            name="Johann Gambolputty... de von Ausfern-schplenden").all()
    """

    def __init__(self, query_cls=None):
        super(FakeSession, self).__init__()
        self.query_cls = query_cls or FakeQuery
        self.db = {}
        self.dirty = []
        self.queries_made = []
        self.flush_called = 0

    def add(self, entity):
        typ = type(entity)
        if typ not in self.db:
            self.db[typ] = []
        super(FakeSession, self).add(entity)

    def add_all(self, entities):
        for entity in entities:
            self.add(entity)

    def delete(self, entity):
        self.deleted.append(entity)

    def flush(self):
        for entity in self.new:
            collection = self.db[type(entity)]
            if entity not in collection:
                collection.append(entity)
        for entity in self.deleted:
            collection = self.db[type(entity)]
            if entity in collection:
                collection.remove(entity)
        self.flush_called += 1
        self.rollback()  # to clear the identity sets

    def rollback(self):
        self.new.clear()
        self.dirty.clear()
        self.deleted.clear()

    def commit(self):
        if self.new or self.deleted:
            self.flush()
        else:
            self.rollback()  # to clear the identity sets


class FakeQuery(BaseFakeQuery):

    def __init__(self, sas, typs):
        super(FakeQuery, self).__init__(sas, typs)
        self.filters = {}
        self.predicates = []
        self.joins = []
        self.orders = []

    def _clone(self):
        """Each method called on query returns a new query which must not
        affect the original.
        """
        clone = super(FakeQuery, self)._clone()
        clone.filters.update(self.filters)
        clone.predicates.extend(self.predicates)
        clone.joins.extend(self.joins)
        clone.orders.extend(self.orders)
        return clone

    def join(self, *typs):
        clone = self._clone()
        clone.joins.extend(typs)
        return clone

    def filter(self, *predicates):
        clone = self._clone()
        clone.predicates.extend(predicates)
        return clone

    def filter_by(self, **filters):
        clone = self._clone()
        clone.filters.update(filters)
        return clone

    def order_by(self, *orders):
        clone = self._clone()
        clone.orders.extend(orders)
        return clone

    def _gen_unordered_results(self):
        # "Log" usage of this query
        self.sas.queries_made.append(self)

        # In autoflush mode, flush is called before a query executes:
        self.sas.flush()

        # For simplicity, right now we only consider the first typ
        first_typ = self.typs[0]
        entities = self.sas.db.get(first_typ, ())
        for entity in entities:
            assert isinstance(entity, first_typ)
            if self._eval_filters(entity) and self._eval_predicates(entity):
                yield entity

    def _eval_filters(self, entity):
        for key, value in self.filters.items():
            assert hasattr(entity, key)
            if getattr(entity, key) != value:
                return False
        return True

    def _eval_predicates(self, entity):
        # TODO predicate matching will fail right now if there are joins
        if self.joins:
            raise NotImplementedError(
                'FakeQuery does not yet return results with joins.')

        for predicate in self.predicates:
            if not self._eval_predicate(entity, predicate):
                return False
        return True

    def _eval_predicate(self, entity, p):
        """Run a .filter() clause/predicate against an entity."""
        # raise NotImplementedError(
        #     'FakeQuery does not yet work with .filter().')
        assert isinstance(p.left, ColumnElement)
        assert isinstance(p.right, BindParameter)
        # cols = [x for x in (p.left, p.right) if isinstance(x, ColumnElement)]
        # if len(cols) != 1:
        #     raise RuntimeError('Not implemented case: cols == {}'.format(cols))
        # param = first((x for x in (p.left, p.right) if isinstance(
        #         x, BindParameter)))
        col = p.left
        param = p.right
        entity_value = getattr(entity, col.name)
        if p.operator is operator.eq:
            # TODO What if names in entity and column differ?
            # TODO Need to find the model with the table of col
            return entity_value == param.value
        elif p.operator.__name__ == 'ilike_op':
            # TODO Deal with wildcards
            return param.value in entity_value
        else:
            raise NotImplementedError(
                "Operator not implemented: {}".format(p.operator.__name__))

    def _gen_ordered_results(self):
        # Reuse _gen_unordered_results() but then respect orders
        raise NotImplementedError(
            'FakeQuery does not yet return ordered results.')

    def __iter__(self):
        if self.orders:
            for x in self._gen_ordered_results():
                yield x
        else:
            for x in self._gen_unordered_results():
                yield x
