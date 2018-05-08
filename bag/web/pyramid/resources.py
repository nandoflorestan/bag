"""Construction kit for Pyramid resource classes.

Example usage::

    from bag.web.pyramid.resources import (
        BaseRootResource, BaseResource, IntResource,
        ancestor, ancestor_model, model_property)
    from pyramid.decorator import reify
    from pyramid.security import (Allow, Deny, Everyone, Authenticated,
                                  ALL_PERMISSIONS)
    from .models import User, Address


    class RootResource(BaseRootResource):
        __acl__ = [
            (Allow, 'group:admin', ALL_PERMISSIONS),
            (Allow, Authenticated, ('view_dashboard', 'edit_users')),
            (Deny, Everyone, ALL_PERMISSIONS),
        ]
        factories = {}  # a static registry of Resource classes


    class UserResource(IntResource):  # /users/1/
        factories = {}  # a static registry of Resource classes

        @reify
        def model(self):
            return sas.query(User).get(self.__name__)

        @reify
        def __acl__(self):
            user_id = self._request.authenticated_userid
            return [(Allow, user_id, self.model.get_permissions(user_id))]


    class UsersResource(BaseResource):  # /users/
        contains_cls = UserResource

        @reify
        def models(self):
            return sas.query(User)

    RootResource.factories['users'] = UsersResource


    class AddressResource(IntResource):  # /users/1/addresses/1
        factories = {}  # a static registry of Resource classes
        model = model_property(sas, Address, user=User)


    class AddressesResource(BaseResource):  # /users/1/addresses
        contains_cls = AddressResource

        @reify
        def models(self):
            return ancestor_model(self, User).addresses

    UserResource.factories['addresses'] = AddressesResource
"""

from bag import first
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPNotFound


def ancestor_finder(resource, predicate, include_self=False):
    """Generate ancestors that satisfy ``predicate``.

    Generator that climbs the tree yielding resources for which
    ``predicate(current_resource)`` returns True.
    """
    resource = resource if include_self else getattr(
        resource, '__parent__', None)
    while resource is not None:
        if predicate(resource):
            yield resource
        resource = getattr(resource, '__parent__', None)


def ancestor(resource, cls, include_self=False):
    """Return the first ancestor of ``resource`` that is of type ``cls``."""
    def predicate(resource):
        return isinstance(resource, cls)
    return first(ancestor_finder(resource, predicate, include_self))


def ancestor_model(resource, cls, include_self=False):
    """Find in ancestors a model instance of type ``cls``.

    The search is done in the ``model`` attribute of the ancestors of
    ``resource``. Returns None if not found.
    """
    def predicate(resource):
        return hasattr(resource, 'model') and isinstance(resource.model, cls)
    o = first(ancestor_finder(resource, predicate, include_self))
    return o.model if o else None


def find_root(resource):
    """Find and return the root resource."""
    return ancestor(resource, type(None))


def model_property(sas, model_cls, **ancestors):
    """Return a property that checks ancestor IDs.

    If you are using SQLAlchemy, this function returns a model property
    that checks some ancestor ID(s) against its foreign key(s). Example usage::

        class AddressResource(BaseResource):
            model = model_property(sas, Address, user=User)
    """
    def wrapped(self):
        o = sas.query(model_cls).get(self.__name__)
        if o is None:
            raise HTTPNotFound()
        for key, cls in ancestors.items():
            if not getattr(o, key) is ancestor_model(self, cls):
                raise HTTPNotFound()
        return o
    return reify(wrapped)


class BaseRootResource:
    """Base class for your Root resource."""

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


class BaseResource(BaseRootResource):
    """Base class for Pyramid traversal resources.

    Subclasses may define a static ``factories`` dict, used to
    map URL elements to other resource classes or factories.
    This is useful for any resource whose children fork into
    separate trees.

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
    """

    def __init__(self):
        """Construct without arguments."""

    def __str__(self):
        return '<{} "{}">'.format(type(self).__name__, self.__name__)

    def __repr__(self):
        alist = []
        for element in reversed(list(ancestor_finder(
                self, lambda resource: True, include_self=True))):
            alist.append(str(element))
        return ' / '.join(alist)


class IntResource(BaseResource):
    """Base class for resources whose name must be an int, e.g. /books/1."""

    def validate_name(self, name):
        try:
            return int(name)
        except ValueError:
            raise KeyError(name)
