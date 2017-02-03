"""Fast unit tests for the bag.sqlalchemy.tricks module.

TODO: Write more tests!
"""

from datetime import datetime
from unittest import TestCase
from sqlalchemy import Column
from sqlalchemy.types import DateTime
from bag.sqlalchemy.tricks import MinimalBase, ID


class SomeModel(MinimalBase, ID):
    """A model class inheriting MinimalBase, for testing."""

    start_date = Column(DateTime)


class TestMinimalBase(TestCase):
    """Tests for the MinimalBase class."""

    def test_tablename(self):
        model = SomeModel()
        assert model.__tablename__ == 'some_model'

    def test_to_dict(self):
        model = SomeModel()
        model.transient = 42  # This datum would not be persisted
        model.start_date = datetime(2016, 12, 4, 8, 46)

        data = {'transient': 42, 'start_date': model.start_date.isoformat()}
        assert model.to_dict() == data