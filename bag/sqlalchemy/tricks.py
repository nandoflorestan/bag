# -*- coding: utf-8 -*-

'''Functions that help define SQLALchemy models.
These have been separated from SQLAlchemy initialization modules because
there are many different ways to initialize SQLALchemy.
'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from decimal import Decimal
import re
from datetime import date, datetime
from sqlalchemy import Table, Column, ForeignKey, Sequence
from sqlalchemy.orm import relationship, MapperExtension, backref as _backref
from sqlalchemy.orm.attributes import (
    CollectionAttributeImpl, ScalarObjectAttributeImpl)
from sqlalchemy.orm.dynamic import DynamicAttributeImpl
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.types import Integer, DateTime, Unicode
from bag import resolve
from nine import basestring
from ..web import gravatar_image

# http://docs.sqlalchemy.org/en/latest/orm/cascades.html
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


def fk(attrib, nullable=False, index=True, primary_key=False, doc=None,
       ondelete='CASCADE'):
    '''Returns a ForeignKey column while automatically setting the type.'''
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
           doc=None, ondelete='CASCADE', backref=None, order_by=None):
    '''Returns a ForeignKey column and a relationship,
        while automatically setting the type of the foreign key.

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
        You may also pass an ``attrib`` which is the column name for
        the foreign key.
        '''
    # http://docs.sqlalchemy.org/en/latest/orm/collections.html#passive-deletes
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
                order_by=order_by))
            if backref else relationship(cls))


def many_to_many(Model1, Model2, pk1='id', pk2='id', metadata=None,
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


def pk(tablename):
    # The type must be Integer for Sequences to work, AFAICT.
    # Maybe this problem is in Python only?
    return Column(Integer, Sequence(tablename + '_id_seq'),
                  primary_key=True, autoincrement=True)


def is_model_class(val):
    return hasattr(val, '__base__') and hasattr(val, '__table__')


def models_and_tables_in(arg):
    '''``arg`` may be a resource spec, a module or a dictionary.

    Returns 2 lists containing the model classes and tables in it::

        models, tables = models_and_tables_in(globals())
    '''
    if not isinstance(arg, dict):
        arg = resolve(arg)  # ensure arg is a python module
        arg = arg.__dict__
    models = [o for o in arg.values() if is_model_class(o)]
    tables = [o for o in arg.values() if isinstance(o, Table)]
    return models, tables


def model_property_names(cls, whitelist=None, blacklist=None,
                         include_relationships=True):
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
    '''Generator that, given a sequence of IDs, yields model instances.'''
    for id in ids:
        yield sas.query(cls).get(id)


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

    def to_dict(self, blacklist=None, whitelist=None, for_json=True):
        '''Dumps the properties of the object into a dict.'''
        props = {}
        blacklist = self.blacklist if blacklist is None else blacklist
        keys = whitelist or self.whitelist or (
            key for key in self.__dict__.keys()
            if not key.startswith('__') and not key.startswith('_sa_'))
        for key in keys:
            if key in blacklist:
                continue
            obj = getattr(self, key)
            if for_json and isinstance(obj, datetime) or isinstance(obj, date):
                props[key] = obj.isoformat()
            elif for_json and isinstance(obj, Decimal):
                props[key] = float(str(obj))
            elif for_json and not isinstance(obj, (
                    basestring, int, float, list, dict, bool, type(None))):
                continue
            else:
                props[key] = obj
        return props
    blacklist = ['password']
    whitelist = None

    def update(self, adict, transient=False):
        '''Applies the information in the provided dictionary to this
            model's properties, optionally checking that the keys exist.
            '''
        for k, v in adict.items():
            if not transient:
                assert hasattr(type(self), k), \
                    "Model {} does not have a '{}' attribute.".format(
                        type(self).__name__, k)
            setattr(self, k, v)
        return self

    def update_from_schema(self, schema, adict):
        '''Validates the information in the dictionary ``adict`` against
            a Colander ``schema``. If validation fails, colander.Invalid
            is raised. If happy, returns the updated model instance.
            '''
        schema._model_instance = self  # makes some validations easier
        clean = schema.deserialize(adict)  # May raise colander.Invalid
        self.update(clean)
        return self

    @classmethod
    def query(cls, sas, *predicates, **filters):
        return sas.query(cls).filter(*predicates).filter_by(**filters)

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
