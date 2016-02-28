# -*- coding: utf-8 -*-

"""Fake objects for unit testing code that uses SQLAlchemy"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from bag import first
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound


class BaseFakeSession(object):
    """Base class for fake SQLAlchemy sessions"""

    def __init__(self):
        self.flush_called = 0
        self.added = []
        self.deleted = []

    def add(self, entity):
        self.added.append(entity)

    def delete(self, entity):
        self.deleted.append(entity)

    def flush(self):
        self.flush_called += 1


class FakeSessionByType(BaseFakeSession):
    """This mock session can be configured to return the results you want
        based on the model type being queried.
        """

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.results = {}

    def query(self, atype):
        self.current_type = atype
        return self

    def join(self, *a, **kw):
        return self

    def filter(self, *a, **kw):
        return self

    filter_by = order_by = filter  # args are ignored

    def all(self):
        return self.results[self.current_type]

    first = all

    def get(self, id):
        for x in self.results[self.current_type]:
            if x.id == id:
                return x
        else:
            return None

    def __iter__(self):
        return self.results[self.current_type].__iter__()


class FakeSession(object):
    """SQLALchemy session mock for quick unit tests.

        Uses lists as an in-memory "database" which can be inspected at the
        end of a unit test.  Tries to behave like autoflush mode.
        """

    def __init__(self, query_cls=None):
        self.query_cls = query_cls or FakeQuery
        self.db = {}
        self.recording = False
        self.new = []
        self.dirty = []
        self.deleted = []
        self.queries_made = []
        self.flush_called = 0

    def add(self, entity):
        typ = type(entity)
        if typ not in self.db:
            self.db[typ] = []
        self.new.append(entity)

    def add_all(self, entities):
        for entity in entities:
            self.add(entity)

    def delete(self, entity):
        self.deleted.append(entity)

    def query(self, *typs):
        return self.query_cls(self, typs)

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


class FakeQuery(object):
    def __init__(self, sas, typs):
        self.sas = sas
        self.typs = typs
        self.filters = {}
        self.predicates = []
        self.joins = []
        self.orders = []

    def _clone(self):
        """Each method called on query returns a new query which must not
            affect the original.
            """
        clone = FakeQuery(self.sas, list(self.typs))
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
            it_matches = True

            for key, value in self.filters.items():
                assert hasattr(entity, key)
                if getattr(entity, key) != value:
                    it_matches = False
                    break

            # TODO predicate matching will fail right now if there are joins
            if self.joins:
                raise NotImplementedError(
                    'FakeQuery does not yet return results with joins.')

            # TODO Consider predicates too
            if self.predicates:
                raise NotImplementedError(
                    'FakeQuery does not yet work with .filter().')
                for p in self.predicates:
                    p.left.name
                    p.operator
                    p.right.value

            if it_matches:
                yield entity

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

    def all(self):
        return list(self)

    def first(self):
        """Returns a matching entity, or None."""
        return first(self)

    def one(self):
        """Ensures there is only one result and returns it, or raises."""
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
