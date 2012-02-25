#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Functions that help define SQLALchemy models.
These have been separated from SQLAlchemy initialization modules because
there are many different ways to initialize SQLALchemy.
'''

from __future__ import absolute_import
from __future__ import unicode_literals  # unicode by default
from datetime import datetime
from sqlalchemy import Column, Sequence
from sqlalchemy.orm import MapperExtension
from sqlalchemy.types import Integer, DateTime

CASC = 'all, delete-orphan'


def id_column(tablename, typ=Integer):
    return Column(typ, Sequence(tablename + '_id_seq'), primary_key=True)


def now_column(nullable=False, **k):
    return Column(DateTime, default=datetime.utcnow, nullable=nullable, **k)


def get_col(model, name):
    '''Introspects the SQLALchemy model `model` and returns the column object
    for the column named `name`. E.g.: col(User, 'email')
    '''
    cols = model._sa_class_manager.mapper.columns
    return cols[name]


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
