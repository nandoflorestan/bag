# -*- coding: utf-8 -*-

'''SQLALchemy initialization for Pyramid applications.

Also crucial is enable_sqlalchemy() in pyramid_starter.py.
'''

from __future__ import unicode_literals  # unicode by default

import transaction
from datetime import datetime
from sqlalchemy import Column, Sequence
from sqlalchemy.types import Integer, DateTime


from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from zope.sqlalchemy import ZopeTransactionExtension
sas = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
del scoped_session
del sessionmaker
del ZopeTransactionExtension


from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()
del declarative_base


# Functions that help defining our models
# =======================================

def id_column(tablename, typ=Integer):
    return Column(typ, Sequence(tablename + '_id_seq'), primary_key=True)


def now_column(nullable=False):
    return Column(DateTime, default=datetime.utcnow, nullable=nullable)


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
