# -*- coding: utf-8 -*-

'''Complete solution for database fixtures using SQLAlchemy.

TODO: Support many-to-many (association tables).
TODO: Improve load_fixtures() ?
'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from codecs import open
from datetime import date, datetime, timedelta
from decimal import Decimal
# from uuid import uuid4
from bag.sqlalchemy.tricks import model_property_names
from nine import nine, str


class IndentWriter(object):
    def __init__(self):
        self.indentation = 0
        self.lines = []

    def indent(self):
        self.indentation += 4

    def dedent(self):
        self.indentation -= 4

    def add(self, line):
        self.lines.append(' ' * self.indentation + line)

    def __str__(self):
        return '\n'.join(self.lines)


@nine
class Mediovaigel(IndentWriter):
    '''Use this to generate SQLAlchemy fixtures from an existing database.
    The fixtures are expressed as Python code, so they sort of self-load.

    You can use Mediovaigel from a Python interpreter::

        from bag.sqlalchemy.mediovaigel import Mediovaigel
        from my.models import Course, Lecture, User, db
        m = Mediovaigel(db.session)
        m.generate_fixtures(Course)
        m.generate_fixtures(Lecture)
        m.generate_fixtures(User, blacklist_props=['id', 'password'])
        # (...)
        print(m.output())
        m.save_to('fixtures/generated.py')
    '''
    def __init__(self, db_session):
        super(Mediovaigel, self).__init__()
        self.sas = db_session
        self.imports = ['import datetime']
        # self.refs = {}
        self.indent()

    def _serialize_property_value(self, entity, attrib, val):
        '''Returns a str containing the representation, or None.

        Override this in subclasses to support other types.
        '''
        if val is None or isinstance(val, (
                int, long, basestring, float, Decimal,
                date, datetime, timedelta)):
            return repr(val)

    def serialize_property_value(self, entity, attrib):
        val = self._serialize_property_value(
            entity, attrib, getattr(entity, attrib))
        if val:
            return val
        else:
            raise RuntimeError(
                'Cannot serialize. Entity: {}. Attrib: {}. Value: {}'.format(
                    entity, attrib, getattr(entity, attrib)))

    def generate_fixtures(self, cls, blacklist_props=['id']):
        '''``cls`` is the model class. ``blacklist_props`` is a list of the
        properties for this class that should be ignored.
        '''
        attribs = model_property_names(cls, blacklist=blacklist_props,
                                       include_relationships=False)
        assert len(attribs) > 0

        self.imports.append('from {} import {}'.format(
            cls.__module__, cls.__name__))
        for entity in self.sas.query(cls).yield_per(50):
            # if hasattr(entity, 'id'):
            #     ref = cls.__name__ + str(entity.id)
            # else:  # If there is no id, we generate our own random id:
            #     ref = cls.__name__ + str(uuid4())[-5:]
            # self.refs[ref] = entity
            # self.add('{} = {}('.format(ref, cls.__name__))
            self.add('yield {}('.format(cls.__name__))
            self.indent()

            for attrib in attribs:
                val = self.serialize_property_value(entity, attrib)
                self.add('{}={},'.format(attrib, val))

            self.dedent()
            self.add(')')
            # self.add('session.add({})\n'.format(ref))

    def output(self, encoding='utf-8'):
        '''Returns the final Python code with the fixture functions.'''
        return STRUCTURE.format(
            encoding=encoding, when=str(datetime.utcnow())[:16],
            imports='\n'.join(self.imports),
            the_fixtures='\n'.join(self.lines),
            )

    def save_to(self, path, encoding='utf-8'):
        with open(path, 'w', encoding=encoding) as writer:
            writer.write(self.output(encoding=encoding))


STRUCTURE = """\
# -*- coding: {encoding} -*-

'''Fixtures autogenerated by Mediovaigel on {when}'''

{imports}


def load_fixtures(session, fixtures=None, flush_every=100):
    for index, entity in enumerate(fixtures or the_fixtures()):
        session.add(entity)
        if index % flush_every == 0:
            print(index)
            session.flush()
    print('Committing...')
    session.commit()


def the_fixtures():
{the_fixtures}
"""
