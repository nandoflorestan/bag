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

**Solution 2:** A more ambitious FakeSession class did not work out and
has been removed already.

**Solution 3:** As of 2016-05, I am sidestepping this as I try to implement
Robert C. Martin's **Clean Architecture** in Python, which forbids I/O
in the center layers of the system. The only place in the system that can
import and use the session is the
`Repository <https://gist.github.com/uris77/4711015>`_,
which is dependency-injected into the service layer. This means the
repository will contain one function per operation or query --
thus it must be easy to mock. This makes the code more testable.
"""

from warnings import warn
from bag import first
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound


warn(
    "bag.sqlalchemy.testing is deprecated. Use repository pattern instead.",
    DeprecationWarning,
)


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
