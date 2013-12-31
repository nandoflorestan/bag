#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Get real database objects and turn them into YAML fixtures for use with
clue_sqlaloader.

Usage::

    from tlc.models import Course
    from bag.sqlalchemy.models2yaml import YamlFixture
    y = YamlFixture()
    # Ignore unwanted properties, especially backrefs:
    y.add_blacklist(Course, ['packages', 'subscriptions', 'disciplines',
                             'progress'])
    y.convert(session.query(Course).all())
    print(y)
'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from datetime import date, datetime
from .tricks import model_property_names


class YamlWriter(object):  # TODO Probably better to use PyYAML instead.
    def __init__(self):
        self.indentation = 0
        self.lines = []

    def indent(self):
        self.indentation += 2

    def dedent(self):
        self.indentation -= 2

    def add(self, line):
        self.lines.append(' ' * self.indentation + line)

    def __str__(self):
        return '\n'.join(self.lines)


class YamlFixture(YamlWriter):
    def __init__(self):
        super(YamlFixture, self).__init__()
        self.blacklists = {}
        self.references = {}

    def add_blacklist(self, cls, props):
        '''Specify that for model class *cls* we should not output values for
        the properties *props*.
        '''
        self.blacklists[cls] = props

    def serialize_property_value(entity, attrib, convert_date=True):
        val = getattr(entity, attrib)
        if val is True:
            return 'true'
        if val is False:
            return 'false'
        if val is None:
            return 'null'
        if convert_date and isinstance(val, datetime) or isinstance(val, date):
            return val.isoformat()
        return val

    def convert(self, models):
        '''Converts a set of model instances to YAML. The results contain
        refnames as long as the original model instance has an "id" attribute.
        '''
        for model in models:
            cls = model.__class__
            qualname = cls.__module__ + '.' + cls.__name__
            self.add('- model: ' + qualname)
            self.indent()
            if hasattr(model, 'id'):
                ref = cls.__name__ + str(model.id)
                self.add('refname: !!refname "{}"'.format(ref))
                # TODO Why am I storing references???
                self.references[ref] = model
            self.add('fields:')
            self.indent()
            for prop in model_property_names(
                    cls, blacklist=self.blacklists.get(cls)):
                val = serialize_property_value(model, prop)
                self.add('{}: {}'.format(prop, val))
            self.dedent()
            self.dedent()
