"""A transparent JSON column for SQLAlchemy models.

The content of this module was basically pasted from
http://docs.sqlalchemy.org/en/latest/orm/extensions/mutable.html
and altered such that the value is never None.
"""

from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.types import TypeDecorator, Unicode
import json


class JSONEncodedDict(TypeDecorator):
    """Represents an immutable structure as a json-encoded string."""

    impl = Unicode

    def process_bind_param(self, value, dialect):
        if value is None:
            value = {}
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            value = {}
        return json.loads(value)


class MutableDict(Mutable, dict):
    """A dict that knows when it gets changed.

    Usage in a SQLAlchemy model::

        data = Column(MutableDict.as_mutable(JSONEncodedDict))
    """

    @classmethod
    def coerce(cls, key, value):
        """Convert plain dictionaries to MutableDict."""
        if value is None:
            value = {}
        if not isinstance(value, MutableDict):
            if isinstance(value, dict):
                return MutableDict(value)

            # This call will raise ValueError
            return Mutable.coerce(key, value)
        else:
            return value

    def __setitem__(self, key, value):
        """Detect dictionary set events and emit change events."""
        dict.__setitem__(self, key, value)
        self.changed()

    def __delitem__(self, key):
        """Detect dictionary del events and emit change events."""
        dict.__delitem__(self, key)
        self.changed()
