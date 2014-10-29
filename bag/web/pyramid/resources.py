# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from nine import nine, str
from bag import first


def ancestor_finder(resource, predicate, include_self=True):
    '''Generator that climbs the tree yielding resources for which
        ``predicate(current_resource)`` returns True.
        '''
    resource = resource if include_self else resource.__parent__
    while resource is not None:
        if predicate(resource):
            yield resource
        resource = getattr(resource, '__parent__', None)


def ancestor(resource, cls, include_self=True):
    def predicate(resource):
        return isinstance(resource, cls)
    return first(ancestor_finder(resource, predicate, include_self))


def ancestor_model(resource, cls, include_self=True):
    '''Returns a model instance found in ancestor.model, or None.'''
    def predicate(resource):
        return hasattr(resource, 'model') and isinstance(resource.model, cls)
    o = first(ancestor_finder(resource, predicate, include_self))
    return o.model if o else o


def find_root(resource):
    return ancestor(resource, type(None))


@nine
class BaseRootResource(object):
    '''Base class for your Root resource.'''
    __name__ = ''
    __parent__ = None

    def __init__(self, request):
        self._request = request

    def __repr__(self):
        return '<{}>'.format(type(self).__name__)

    def _make_descendant(self, factory, name):
        o = factory()
        o._request = self._request
        o.__parent__ = self
        if hasattr(o, 'validate_name'):
            o.__name__ = o.validate_name(name)
        else:
            o.__name__ = name
        return o

    def __getitem__(self, name):
        if hasattr(self, 'contains_cls'):
            return self._make_descendant(self.contains_cls, name)
        elif hasattr(self, 'factories'):
            return self._make_descendant(self.factories[name], name)
        raise KeyError(name)

    # TODO Remove these eventually. It's better to use the functions.
    ancestor = ancestor
    ancestor_model = ancestor_model


@nine
class BaseResource(BaseRootResource):
    '''Base class for Pyramid traversal resources.

        Subclasses may define a static ``factories`` dict, used to
        map URL elements to other resource classes or factories.
        This is mainly useful for the root resource which usually
        forks into several separate trees.

        Subclasses may also represent collections, such as /books/.
        These subclasses must define a ``contains_cls`` attribute,
        whose value is to be the contained resource class.

        For a subclass representing a single model instance ―
        e. g. /books/1/ ―, you can implement a ``model`` property;
        then a descendant view such as /books/1/authors/ may call
        ``ancestor_model(Book)``, which will find the ancestor and
        return the ``model`` property value. Example::

            @reify
            def model(self):
                return sas.query(Book).get(self.__name__)
        '''

    def __init__(self):
        '''Constructor without arguments.'''

    def __str__(self):
        return '<{} "{}">'.format(type(self).__name__, self.__name__)

    def __repr__(self):
        alist = []
        for element in reversed(list(ancestor_finder(
                self, lambda resource: True))):
            alist.append(str(element))
        return ' / '.join(alist)


class IntResource(BaseResource):
    '''Base class for resources whose name must be an integer, e.g. /books/1'''

    def validate_name(self, name):
        try:
            return int(name)
        except ValueError:
            raise KeyError(name)
