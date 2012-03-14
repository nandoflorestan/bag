#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Demonstration and correction of a colander 0.9.2 - 0.9.6 bug.'''

from __future__ import (absolute_import, division, print_function,
    unicode_literals)
import unittest
import colander as c
from bag.six import *

# TODO: Make a TestSuite that includes the colander test suite.


class EditSchema(c.MappingSchema):
    minLength = c.SchemaNode(c.Int(), validator=c.Range(min=1), missing=1)
    maxLength = c.SchemaNode(c.Int(), validator=c.Range(min=1), missing=800)
    minWords = c.SchemaNode(c.Int(), validator=c.Range(min=1), missing=1)
    maxWords = c.SchemaNode(c.Int(), validator=c.Range(min=1), missing=400)


# Validators
def validate_length(node, val):
    if val['minLength'] > val['maxLength']:
        e = c.Invalid(node, 'Length inconsistency')
        e['minLength'] = 'Higher than max length'
        raise e

def validate_words(node, val):
    if val['minWords'] > val['maxWords']:
        e = c.Invalid(node, 'Word count inconsistency')
        e['minWords'] = 'Higher than max words'
        raise e
edit_schema = EditSchema(validator=c.All(validate_length, validate_words))


class TestColander(unittest.TestCase):
    def test_colander(self):
        from bag.web.pyramid.deform import monkeypatch_colander
        monkeypatch_colander()
        expected_asdict = {
            'minLength': 'Length inconsistency; Word count inconsistency; Higher than max length',
            'minWords': 'Length inconsistency; Word count inconsistency; Higher than max words',
        }
        expected_asdict2 = {
            '': 'Word count inconsistency; Length inconsistency',
            'minLength': 'Higher than max length',
            'minWords': 'Higher than max words',
        }
        try:
            edit_schema.deserialize(dict(
                minLength=2, maxLength=1, minWords=2, maxWords=1
            ))
        except c.Invalid as e:
            self.assertEqual(e.asdict(), expected_asdict)
            self.assertEqual(e.asdict2(), expected_asdict2)
        else:
            # Ops, Invalid was NOT raised, that is a problem. :(
            self.assertTrue(False)
            '''Traceback (most recent call last):
  File "/home/nando/py/my/bag/bag/tests/test_colander.py", line 51, in test_colander
    self.assertEqual(e.asdict(), expected_asdict)
  File "/home/nando/py/lib/colander-0.9.6-py2.7.egg/colander/__init__.py", line 165, in asdict
    errors['.'.join(keyparts)] = '; '.join(interpolate(msgs))
TypeError: sequence item 0: expected string, list found

'''
