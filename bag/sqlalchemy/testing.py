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
