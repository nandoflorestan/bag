# -*- coding: utf-8 -*-

'''Fake objects for unit testing code that uses SQLAlchemy'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


class FakeSession(object):
    '''Fake SQLAlchemy session'''

    def __init__(self):
        self.flush_called = 0
        self.added = []

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        self.flush_called += 1


class FakeSessionByType(FakeSession):
    '''This mock session can be configured to return the results you want
        based on the model type being queried.
        '''

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.results = {}

    def query(self, atype):
        self.current_type = atype
        return self

    def filter(self, *a, **kw):
        return self

    filter_by = order_by = filter

    def all(self):
        return self.results[self.current_type]

    first = all

    def get(self, id):
        return self.results[self.current_type]

    def __iter__(self):
        return self.results.__iter__()
