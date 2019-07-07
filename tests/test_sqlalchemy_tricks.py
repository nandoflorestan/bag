"""Fast unit tests for the bag.sqlalchemy.tricks module.

TODO: Write more tests!
"""

from unittest import TestCase

from sqlalchemy import Column
from sqlalchemy.types import DateTime

from bag.sqlalchemy.tricks import ID, MinimalBase


class SomeModel(MinimalBase, ID):
    """A model class inheriting MinimalBase, for testing."""

    start_date = Column(DateTime)


class TestMinimalBase(TestCase):
    """Tests for the MinimalBase class."""

    def test_tablename(self):
        model = SomeModel()
        assert model.__tablename__ == 'some_model'
