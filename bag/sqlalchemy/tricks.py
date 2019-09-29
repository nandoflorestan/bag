"""Functions that help define SQLAlchemy models."""

import re
from datetime import datetime
from typing import List, Tuple, Union
from warnings import warn

from sqlalchemy import Table, Column, ForeignKey, Sequence
from sqlalchemy.orm import backref as _backref, class_mapper, ColumnProperty
from sqlalchemy.orm.attributes import (
    CollectionAttributeImpl, ScalarObjectAttributeImpl)
from sqlalchemy.orm.dynamic import DynamicAttributeImpl
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.types import Integer, DateTime, Unicode

from bag.settings import resolve
from bag.web.exceptions import Problem
from ..web import gravatar_image

# http://docs.sqlalchemy.org/en/latest/orm/cascades.html
CASC = 'all, delete-orphan'


def now_column(nullable: bool=False, **k) -> Column:
    """Return a DateTime column that defaults to utcnow."""
    return Column(DateTime, default=datetime.utcnow, nullable=nullable, **k)


def get_col(model, attribute_name):
    """Introspect the SQLAlchemy ``model``; return the column object.

    ...for ``attribute_name``. E.g.: ``get_col(User, 'email')``
    """
    return model._sa_class_manager.mapper.columns[attribute_name]


def _get_length(col):
    return None if col is None else getattr(col.type, 'length', None)


def get_length(model, field):
    """Return the length of column ``field`` of a SQLAlchemy ``model``."""
    return _get_length(get_col(model, field))


def col(attrib):
    """Return the column that stores an ``attrib`` of a model.

    Given a sqlalchemy.orm.attributes.InstrumentedAttribute
    (type of the attributes of model classes),
    return the corresponding column. E.g.: ``col(User.email)``
    """
    return attrib.property.columns[0]


def length(attrib):
    """Return the length of the ``attrib``."""
    return _get_length(col(attrib))


def fk(attrib, nullable=False, index=True, primary_key=False, doc=None,
       ondelete='CASCADE'):
    """Return a ForeignKey column while automatically setting the type."""
    assert ondelete in (
        'CASCADE',   # Creates ON DELETE CASCADE
        'SET NULL',  # Creates ON DELETE SET NULL
        None,        # Creates ON DELETE NO ACTION, with more runtime errors
        )
    column = col(attrib)
    return Column(
        column.copy().type, ForeignKey(column, ondelete=ondelete),
        doc=doc, index=index, primary_key=primary_key, nullable=nullable)


def fk_rel(cls, attrib='id', nullable=False, index=True, primary_key=False,
           doc=None, ondelete='CASCADE', backref=None, order_by=None,
           lazy='select'):
    """Return a ForeignKey column and a relationship.

    Automatically sets the type of the foreign key.

    Usage::

        # A relationship in an Address model pointing to a parent Person:
        person_id, person = fk_rel(Person, nullable=False,
            index=True, backref='addresses', ondelete='CASCADE')

    A backref is created only if you provide its name in the argument.
    ``nullable`` and ``index`` are usually ommited, because these are the
    default values and they are good.

    ``ondelete`` is "CASCADE" by default, but you can set it to "SET NULL",
    or None which translates to "NO ACTION" (less interesting).
    If provided, ``order_by`` is used on the backref.

    To load the backref greedily, use ``lazy='joined'`` as per
    http://docs.sqlalchemy.org/en/latest/orm/loading_relationships.html

    You may also pass an ``attrib`` which is the column name for
    the foreign key.
    """
    # http://docs.sqlalchemy.org/en/latest/orm/collections.html#passive-deletes
    from sqlalchemy.orm import relationship
    if ondelete == 'CASCADE':
        cascade = CASC
        passive_deletes = True
    else:
        cascade = False  # meaning "save-update, merge"
        passive_deletes = False

    return (fk(getattr(cls, attrib), nullable=nullable, index=index,
               primary_key=primary_key, doc=doc, ondelete=ondelete),
            relationship(cls, backref=_backref(
                backref, cascade=cascade, passive_deletes=passive_deletes,
                order_by=order_by, lazy=lazy))
            if backref else relationship(cls))


def many_to_many(Model1, Model2, pk1='id', pk2='id', metadata=None,
                 backref=None):
    """Easily set up a many-to-many relationship between 2 existing models.

    Return an association table and the relationship itself.

    Usage:

        customer_user, Customer.users = many_to_many(Customer, User,
            pk2='__id__')
    """
    from sqlalchemy.orm import relationship
    table1 = Model1.__tablename__
    table2 = Model2.__tablename__
    col1 = col(getattr(Model1, pk1))
    col2 = col(getattr(Model2, pk2))
    type1 = col1.copy().type
    type2 = col2.copy().type
    metadata = metadata or Model1.__table__.metadata
    association = Table(
        table1 + '_' + table2, metadata,
        Column(table1 + '_id', type1, ForeignKey(table1 + '.' + col1.name),
               nullable=False, index=True),
        Column(table2 + '_id', type2, ForeignKey(table2 + '.' + col2.name),
               nullable=False, index=True),
    )
    backref = backref or table1 + 's'
    rel = relationship(Model2, secondary=association, backref=backref)
    return association, rel


def pk(tablename: str) -> Column:
    """Return a primary key column."""
    # The type must be Integer for Sequences to work, AFAICT.
    # Maybe this problem is in Python only?
    return Column(Integer, Sequence(tablename + '_id_seq'),
                  primary_key=True, autoincrement=True)


def is_model_class(val) -> bool:
    """Return whether the parameter is a SQLAlchemy model class."""
    return hasattr(val, '__base__') and hasattr(val, '__table__')


def models_and_tables_in(arg) -> Tuple[List, List]:
    """Return 2 lists containing the model classes and tables in ``arg``.

    ``arg`` may be a resource spec, a module or a dictionary::

        models, tables = models_and_tables_in(globals())
    """
    if not isinstance(arg, dict):
        arg = resolve(arg)  # ensure arg is a python module
        arg = arg.__dict__
    models = [o for o in arg.values() if is_model_class(o)]
    tables = [o for o in arg.values() if isinstance(o, Table)]
    return models, tables


def model_property_names(cls, whitelist=None, blacklist=None,
                         include_relationships=True):
    """Return the property names in the passed class, maybe filtered."""
    names = (str(n).split('.')[1] for n in cls.__mapper__.iterate_properties)
    filtered = []
    for name in names:
        if blacklist and name in blacklist:
            continue
        if whitelist and name not in whitelist:
            continue
        if not include_relationships and isinstance(
                getattr(cls, name).impl, (
                    CollectionAttributeImpl, DynamicAttributeImpl,
                    ScalarObjectAttributeImpl)):
            continue
        filtered.append(name)
    return filtered


def foreign_key_from_col(col):
    # I don't know how there would ever be more than one item in this, so:
    for fk in col.foreign_keys:  # foreign_keys is, strangely, a set
        return fk


def foreign_keys_in(cls):
    filtered = {}
    for name in model_property_names(cls, include_relationships=False):
        a_set = getattr(cls, name).expression.foreign_keys
        for fk in a_set:
            # I don't understand why there would ever be more than one item
            # in this, so:
            filtered[name] = fk
            break
    return filtered


def models_from_ids(sas, cls, ids):
    """Generator that, given a sequence of IDs, yields model instances.

    Performance is poor. TODO SOMEONE IMPROVE THIS PLEASE
    """
    for id in ids:
        yield sas.query(cls).get(id)


def persistent_attribute_names_of(cls):
    """Return a list of the names of the persistent attributes of ``cls``.

    ...except collections.
    """
    # return [x for x in dir(cls) if isinstance(
    #     getattr(cls, x), InstrumentedAttribute)]
    return [
        prop.key for prop in class_mapper(cls).iterate_properties
        if isinstance(prop, ColumnProperty)]


class MinimalBase:
    """Declarative base class that auto-generates __tablename__."""

    __table_args__: Union[dict, tuple] = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8",
    }

    @declared_attr
    def __tablename__(cls):
        """Convert CamelCase class to underscores_between_words table name."""
        name = cls.__name__.replace('Mixin', '')
        return name[0].lower() + \
            re.sub(r'([A-Z])', lambda m: "_" + m.group(0).lower(), name[1:])

    def update(self, adict, transient=False):
        """Merge dictionary into this entity.

        Optionally check that the keys exist.
        """
        for k, v in adict.items():
            if not transient:
                assert hasattr(type(self), k), \
                    "Model {} does not have a '{}' attribute.".format(
                        type(self).__name__, k)
            setattr(self, k, v)
        return self

    def update_from_schema(self, schema, adict):
        """Validate ``adict`` against ``schema``; return updated entity.

        Validates the information in the dictionary ``adict`` against
        a Colander ``schema``. If validation fails, colander.Invalid
        is raised. If happy, returns the updated model instance.
        """
        schema._model_instance = self  # makes some validations easier
        clean = schema.deserialize(adict)  # May raise colander.Invalid
        self.update(clean)
        return self

    @classmethod
    def get_or_create(cls, session, **filters):
        """Retrieve or add object; return a tuple ``(object, is_new)``.

        ``is_new`` is True if the object already exists in the database.
        """
        warn(
            "get_or_create() is deprecated and will be removed, because "
            "model methods should not use the SQLAlchemy session.",
            DeprecationWarning
        )
        instance = session.query(cls).filter_by(**filters).first()
        is_new = not instance
        if is_new:
            instance = cls(**filters)
            session.add(instance)
        return instance, is_new

    @classmethod
    def create_or_update(cls, session, values={}, **filters):
        """Load and update entity if it exists, else create one.

        First obtains either an existing object or a new one, based on
        ``filters``. Then applies ``values`` and returns a tuple
        ``(object, is_new)``.
        """
        warn(
            "create_or_update() is deprecated and will be removed, because "
            "model methods should not use the SQLAlchemy session.",
            DeprecationWarning
        )
        instance, is_new = cls.get_or_create(session, **filters)
        for k, v in values.items():
            setattr(instance, k, v)
        return instance, is_new

    def update_association(
        self, sas, cls, field, ids, filters={}, synchronize_session=None,
    ):
        """When you have a many-to-many relationship, there is an association
        table between 2 main tables. The problem of setting the data in
        this case is a recurring one and it is solved here.
        Some associations might be deleted and some might be created.

        Example usage::

            user = session.query(User).get(1)
            # Suppose there's a many-to-many relationship to Address,
            # named UserAddress.
            new_associations = user.update_association(
                sas,                 # the SQLAlchemy session
                cls=UserAddress,      # the association class
                field='address_id'     # name of the remote foreign key
                ids=[5, 42, 89],        # the IDs of the user's addresses
                filters={"user": user},  # to load existing associations
                )
            for item in new_associations:
                print(item)

        This method returns a list of any new association instances
        because you might want to finish the job by doing something
        more with them (e. g. setting other attributes).

        A new query is needed to retrieve the totality of the associations.
        """
        warn(
            "update_association() is deprecated and will be removed, because "
            "model methods should not use the SQLAlchemy session.",
            DeprecationWarning
        )
        # Fetch eventually existing association IDs
        existing_ids = frozenset([
            o[0] for o in sas.query(getattr(cls, field)).filter_by(**filters)])

        # Delete association rows that we no longer want
        desired_ids = frozenset(ids)
        to_remove = existing_ids - desired_ids
        q_remove = sas.query(cls).filter_by(**filters).filter(
            getattr(cls, field).in_(to_remove))
        if to_remove and synchronize_session is not None:
            q_remove.delete(synchronize_session=synchronize_session)
        else:
            for entity in q_remove:
                sas.delete(entity)

        # Create desired associations that do not yet exist
        to_create = desired_ids - existing_ids
        new_associations = []
        for id in to_create:
            association = cls(**filters)
            setattr(association, field, id)
            new_associations.append(association)
        sas.add_all(new_associations)
        return new_associations

    def clone(self, values=None, pk='id', sas=None):
        """Return a clone of this model.

        Optionally update some of its ``values``.
        Optionally add the clone to the ``sas`` session.
        The name of the primary key column should be given as ``pk``.
        """
        attrs = persistent_attribute_names_of(self.__class__)
        adict = {}
        for attr in attrs:
            adict[attr] = getattr(self, attr)
        if pk:
            del adict[pk]
        if values:
            adict.update(values)
        clone = self.__class__(**adict)
        if sas:  # Optionally add the clone to the SQLAlchemy session
            warn(
                "The sas argument of clone() is deprecated and "
                "will be removed.",
                DeprecationWarning
            )
            sas.add(clone)
        return clone


class ID:
    """Mixin class that includes a primary key column "id"."""

    @declared_attr
    def id(cls):
        """Primary key column for your model."""
        return Column(Integer, autoincrement=True, primary_key=True)


class Names:
    """Mixin class that includes 2 ways to handle a person's names."""

    @declared_attr
    def full_name(cls):  # noqa
        return Column(Unicode(120), nullable=False)

    @declared_attr
    def short_name(cls):  # noqa
        return Column(Unicode(16), nullable=False)

    @property
    def display_name(self):  # noqa
        return self.short_name or self.full_name

    @property
    def formal_name(self):  # noqa
        return self.full_name or self.short_name


class AddressBase:
    """Base class for addresses.

    In subclasses you can just define ``__tablename__``, ``id``,
    the foreign key, and maybe indexes.
    """

    # __tablename__ = 'customer'

    # pk = pk(__tablename__)
    street = Column('street',     Unicode(160), default='')
    district = Column('district', Unicode(80),  default='')
    city = Column('city',         Unicode(80), default='')
    province = Column('province', Unicode(40), default='')
    country_code = Column('country_code', Unicode(2), default='')
    postal_code = Column('postal_code',  Unicode(16), default='',
                         doc='Zip code')
    # kind = Column(Unicode(1), default='',
    #     doc="c for commercial, r for residential")
    # charge = Column(Boolean, default=False,
    #     doc="Whether this is the address to bill to.")
    # comment = Column(Unicode, default='')


class EmailParts:
    """Mixin class that stores an email address in 2 columns.

    One column contains the local part, another contains the domain.
    This makes it easy to find emails from the same domain.

    Typical usage:

    .. code-block:: python

        class Customer(SABase, EmailParts):
            __table_args__ = (UniqueConstraint('email_local', 'email_domain',
                              name='customer_email_key'), {})
    """

    email_local = Column('email_local',   Unicode(160), nullable=False)
    email_domain = Column('email_domain', Unicode(255), nullable=False)

    @hybrid_property
    def email(self):
        """Get or set the entire email, in Python or in the RDBMS."""
        return self.email_local + '@' + self.email_domain

    @email.setter
    def set_email(self, val):
        self.email_local, self.email_domain = val.split('@')
        if not self.email_local:
            raise Problem('Missing the local part of the email address.')
        if not self.email_domain:
            raise Problem('Missing the domain part of the email address.')

    def gravatar_image(
        self, default: str = 'mm', size: int = 80, cacheable: bool = True,
    ) -> str:
        """Return the URL for the gravatar image for this email address."""
        return gravatar_image(self.email, default=default, size=size,
                              cacheable=cacheable)


def commit_session_or_transaction(sas) -> None:
    """Not sure if using the transaction package or not? No problem."""
    try:
        sas.commit()
    except AssertionError as exc:
        if str(exc) == 'Transaction must be committed using ' \
                       'the transaction manager':
            import transaction
            transaction.commit()
        else:
            raise


class SubtransactionTrick:
    """Encloses your code in a subtransaction. Good for writing tests.

    Usage::

        trick = SubtransactionTrick(my_engine, sessionmaker)
        # Be sure to use the session provided as the ``sas`` variable:
        my_session = trick.sas
        # Finally, call ``close()`` to roll back the changes:
        trick.close()
    """

    def __init__(self, engine, sessionmaker):
        """Constructor.

        - ``engine`` should be a completely configured SQLAlchemy engine.
        - ``sessionmaker`` should be a session factory that can be bound
          to a specific connection.
        """
        self.connection = engine.connect()

        # begin a non-ORM transaction
        self.transaction = self.connection.begin()
        # Base.metadata.bind = connection

        # bind an individual Session to the connection
        if hasattr(sessionmaker, 'query'):  # scoped session detected
            sessionmaker.configure(bind=self.connection)
            self.sas = sessionmaker
        else:  # not a scoped session
            self.sas = sessionmaker()(bind=self.connection)

    def close(self):
        """Roll back everything that happened with the session.

        ...including calls to commit().
        """
        self.transaction.rollback()
        self.sas.close()
        # self.connection.close()
