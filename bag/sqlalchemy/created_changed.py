"""SQLAlchemy trick that makes it easy to implement timestamp columns.

Usage::

    from bag.sqlalchemy.created_changed import created_changed, CreatedChanged

    @created_changed
    class MyModel(BaseModel, CreatedChanged):
        ...
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, event


class CreatedChanged:
    """Mixin class that adds ``created`` and ``changed`` columns.

    Must be used together with the ``@created_changed`` class decorator.
    """

    created = Column(DateTime, nullable=False)
    changed = Column(DateTime, nullable=False)


def created_changed(cls):
    """Decorate ``cls`` to update *created* and *changed* automatically.

    If you use SQLAlchemy inheritance, apply this decorator to subclasses.
    """
    def _set_created_and_changed(mapper, connection, instance):
        instance.created = instance.changed = datetime.utcnow()

    def _set_changed(mapper, connection, instance):
        instance.changed = datetime.utcnow()

    event.listen(cls, 'before_insert', _set_created_and_changed)
    event.listen(cls, 'before_update', _set_changed)
    return cls
