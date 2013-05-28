# -*- coding: utf-8 -*-

'''Functions that help define SQLALchemy models.
These have been separated from SQLAlchemy initialization modules because
there are many different ways to initialize SQLALchemy.
'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import re
from datetime import date, datetime
from sqlalchemy import Table, Column, ForeignKey, Sequence
from sqlalchemy.orm import relationship, MapperExtension
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.types import Integer, DateTime, Unicode
from ..web import gravatar_image

# http://docs.sqlalchemy.org/en/latest/orm/session.html#cascades
CASC = 'all, delete-orphan'


def now_column(nullable=False, **k):
    return Column(DateTime, default=datetime.utcnow, nullable=nullable, **k)


def get_col(model, attribute_name):
    '''Introspects the SQLALchemy model *model* and returns the column object
    for *attribute_name*. E.g.: ``get_col(User, 'email')``
    '''
    return model._sa_class_manager.mapper.columns[attribute_name]


def _get_length(col):
    return None if col is None else getattr(col.type, 'length', None)


def get_length(model, field):
    '''Returns the length of column *field* of a SQLAlchemy model *model*.'''
    return _get_length(get_col(model, field))


def col(attrib):
    '''Given a sqlalchemy.orm.attributes.InstrumentedAttribute
    (type of the attributes of model classes),
    returns the corresponding column. E.g.: ``col(User.email)``
    '''
    return attrib.property.columns[0]


def length(attrib):
    '''Returns the length of the attribute *attrib*.'''
    return _get_length(col(attrib))


def fk(attrib, nullable=False, index=True):
    '''Returns a ForeignKey column while automatically setting the type.'''
    column = col(attrib)
    return Column(column.copy().type, ForeignKey(column),
                  nullable=nullable, index=index)


def fk_rel(cls, backref=None, attrib='pk', nullable=False, index=True):
    '''Returns a ForeignKey column and a relationship,
    while automatically setting the type of the foreign key.

    Usage::

        # A relationship in an Address model:
        person_id, person = fk_rel(Person, 'addresses',
            nullable=False, index=True)
        # *nullable* and *index* are usually ommited, because
        # these are the default values and they are good.
    '''
    return (fk(getattr(cls, attrib), nullable=nullable, index=index),
        relationship(cls, backref=backref))


def many_to_many(Model1, Model2, pk1='pk', pk2='pk', metadata=None,
                 backref=None):
    '''Easily set up a many-to-many relationship between 2 existing models.

    Returns an association table and the relationship itself.

    Usage:

        customer_user, Customer.users = many_to_many(Customer, User,
            pk2='__id__')
    '''
    table1 = Model1.__tablename__
    table2 = Model2.__tablename__
    col1 = col(getattr(Model1, pk1))
    col2 = col(getattr(Model2, pk2))
    type1 = col1.copy().type
    type2 = col2.copy().type
    metadata = metadata or Model1.__table__.metadata
    association = Table(table1 + '_' + table2, metadata,
        Column(table1 + '_id', type1, ForeignKey(table1 + '.' + col1.name),
            nullable=False, index=True),
        Column(table2 + '_id', type2, ForeignKey(table2 + '.' + col2.name),
            nullable=False, index=True),
    )
    backref = backref or table1 + 's'
    rel = relationship(Model2, secondary=association, backref=backref)
    return association, rel


def pk(tablename):
    # The type must be Integer for Sequences to work, AFAICT.
    # Maybe this problem is in Python only?
    return Column(Integer, Sequence(tablename + '_id_seq'),
        primary_key=True, autoincrement=True)


class MinimalBase(object):
    """Declarative base class that auto-generates __tablename__."""
    __table_args__ = dict(mysql_engine='InnoDB', mysql_charset='utf8')

    @declared_attr
    def __tablename__(cls):
        """Convert the CamelCase class name to an underscores_between_words
        table name.
        """
        name = cls.__name__.replace('Mixin', '')
        return name[0].lower() + \
            re.sub(r'([A-Z])', lambda m: "_" + m.group(0).lower(), name[1:])

    def to_dict(self, blacklist=None, convert_date=False):  # TODO Whitelist
        """Dumps the properties of the object into a dict for use in json."""
        props = {}
        for key in self.__dict__:
            if key in (blacklist or self.blacklist) or key.startswith('__') \
                    or key.startswith('_sa_'):
                continue
            obj = getattr(self, key)
            if isinstance(obj, datetime) or isinstance(obj, date):
                if convert_date:
                    props[key] = obj.isoformat()
                else:
                    props[key] = obj
            else:
                props[key] = obj
        return props
    blacklist = ['password']

    @classmethod
    def get_or_create(cls, session, **filters):
        '''Returns a tuple (object, is_new). *is_new* is True if the
        object already exists in the database.
        '''
        instance = session.query(cls).filter_by(**filters).first()
        is_new = not instance
        if is_new:
            instance = cls(**filters)
            session.add(instance)
        return instance, is_new

    @classmethod
    def create_or_update(cls, session, values={}, **filters):
        '''First obtains either an existing object or a new one, based on
        *filters*. Then applies *values* and returns a tuple (object, is_new).
        '''
        instance, is_new = cls.get_or_create(session, **filters)
        for k, v in values.items():
            setattr(instance, k, v)
        return instance, is_new

    @classmethod
    def count(cls, session, **filters):
        return session.query(cls).filter_by(**filters).count()


class PK(object):
    '''Mixin class that includes a primary key column.'''
    @declared_attr
    def pk(cls):
        '''We use "pk" instead of "id" because "id" is a python builtin.'''
        return Column(Integer, autoincrement=True, primary_key=True)


class ID(object):
    '''Mixin class that includes a primary key column "id".'''
    @declared_attr
    def id(cls):
        '''So many projects out there are using "id" instead of "pk"...'''
        return Column(Integer, autoincrement=True, primary_key=True)


class CreatedChanged(object):
    '''Mixin class for your models. It updates the *created* and *changed*
    columns automatically.

    If you define __mapper_args__ in your model, you have to readd the
    mapper extension:

    .. code-block:: python

        __mapper_args__ = dict(order_by=name,
            extension=CreatedChanged.MapperExt())
    '''
    created = Column(DateTime, nullable=False)
    changed = Column(DateTime, nullable=False)

    class MapperExt(MapperExtension):
        def before_insert(self, mapper, connection, instance):
            instance.created = instance.changed = datetime.utcnow()

        def before_update(self, mapper, connection, instance):
            instance.changed = datetime.utcnow()
    __mapper_args__ = dict(extension=MapperExt())
# http://www.devsniper.com/sqlalchemy-tutorial-3-base-entity-class-in-sqlalchemy/


class AddressBase(object):
    '''Base class for addresses. In subclasses you can just define
    __tablename__, id, the foreign key, and maybe indexes.
    '''
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


class EmailParts(object):
    '''Mixin class that stores an email address in 2 columns,
    one for the local part, one for the domain. This makes it easy to
    find emails from the same domain.

    Typical usage:

    .. code-block:: python

        class Customer(SABase, EmailParts):
            __table_args__ = (UniqueConstraint('email_local', 'email_domain',
                              name='customer_email_key'), {})
    '''
    email_local = Column('email_local',   Unicode(160), nullable=False)
    email_domain = Column('email_domain', Unicode(255), nullable=False)

    @hybrid_property
    def email(self):
        return self.email_local + '@' + self.email_domain

    @email.setter
    def email(self, val):
        self.email_local, self.email_domain = val.split('@')

    def gravatar_image(self, default='mm', size=80, cacheable=True):
        return gravatar_image(self.email, default=default, size=size,
            cacheable=cacheable)
