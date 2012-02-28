#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Functions that help define SQLALchemy models.
These have been separated from SQLAlchemy initialization modules because
there are many different ways to initialize SQLALchemy.
'''

from __future__ import absolute_import
from __future__ import unicode_literals  # unicode by default
from datetime import datetime
from sqlalchemy import Table, Column, ForeignKey, Sequence
from sqlalchemy.orm import relationship, MapperExtension
from sqlalchemy.types import Integer, DateTime, Unicode

CASC = 'all, delete-orphan'


def id_column(tablename, typ=Integer):
    return Column(typ, Sequence(tablename + '_id_seq'), primary_key=True)


def now_column(nullable=False, **k):
    return Column(DateTime, default=datetime.utcnow, nullable=nullable, **k)


def get_col(model, attribute_name):
    '''Introspects the SQLALchemy model *model* and returns the column object
    for *attribute_name*. E.g.: col(User, 'email')
    '''
    return model._sa_class_manager.mapper.columns[attribute_name]


def _get_length(col):
    return None if col is None else getattr(col.type, 'length', None)


def get_length(model, field):
    '''Returns the length of column `field` of a SQLAlchemy model `model`.'''
    return _get_length(get_col(model, field))


def col(attrib):
    '''Given a sqlalchemy.orm.attributes.InstrumentedAttribute
    (type of the attributes of model classes),
    returns the corresponding column. E.g.: col(User.email)
    '''
    return attrib.property.columns[0]


def length(attrib):
    '''Returns the length of the attribute `attrib`.'''
    return _get_length(col(attrib))


def many_to_many(Model1, Model2, id_attr1='id', id_attr2='id', metadata=None,
                 backref=None):
    '''Easily set up a many-to-many relationship between 2 existing models.

    Returns an association table and the relationship itself.
    '''
    table1 = Model1.__tablename__
    table2 = Model2.__tablename__
    col1 = col(getattr(Model1, id_attr1))
    col2 = col(getattr(Model2, id_attr2))
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


class CreatedChanged(object):
    '''Mixin class for your models.'''
    created = Column(DateTime, nullable=False)
    changed = Column(DateTime, nullable=False)

    class CreatedChangedMapperExt(MapperExtension):
        def before_insert(self, mapper, connection, instance):
            instance.created = instance.changed = datetime.utcnow()

        def before_update(self, mapper, connection, instance):
            instance.changed = datetime.utcnow()
    __mapper_args__ = dict(extension=CreatedChangedMapperExt())
# http://www.devsniper.com/sqlalchemy-tutorial-3-base-entity-class-in-sqlalchemy/


class AddressBase(object):
    '''Base class for addresses. In subclasses you can just define
    __tablename__, id, the foreign key, and maybe indexes.
    '''
    #~ __tablename__ = 'customer'

    #~ id = id_column(__tablename__)
    street = Column(Unicode(160), default='')
    district = Column(Unicode(80), default='')
    city = Column(Unicode(80), default='')
    province = Column(Unicode(40), default='')
    country_code = Column(Unicode(2), default='')
    zipcode = Column(Unicode(16), default='')
    # kind = Column(Unicode(1), default='',
    #     doc="c for commercial, r for residential")
    # charge = Column(Boolean, default=False,
    #     doc="Whether this is the address to bill to.")
    # comment = Column(Unicode, default='')
