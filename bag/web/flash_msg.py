# -*- coding: utf-8 -*-

"""FlashMessage is the natural class to store UI notifications since it knows:

- the content of a flash message in either plain or rich form(s)
- the kind (color) of the message, such as info, danger, success etc.
- different ways of rendering the message on the page
- whatever else you want (you can add instance variables or subclass it).

This can be used in any web framework. We provide integration for Pyramid
in the module :mod:`bag.web.pyramid.flash_msg`.

FlashMessage is able to render itself with Bootstrap styles.

If you are not using Bootstrap, or if you don't like that I am
generating HTML in Python, or if you want some additional content or style,
you can still use this class and just render the messages yourself.
You can even override the ``bootstrap_alert`` property in a subclass.
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from cgi import escape
from copy import copy
from nine import nine, basestring


def bootstrap_alert(plain=None, rich=None, kind='warning', close=True, v=3):
    """Renders a bootstrap alert message, optionally with a close button.
        Provide either ``plain`` or ``rich`` content. The parameter ``v``
        can be 3 or 2 depending on your bootstrap version (default 3).
        """
    # In bootstrap 3, the old "error" class becomes "danger":
    if kind == 'danger' and v == 2:
        kind = 'error'

    return '<div class="alert alert-{kind}{cls} fade in">{close}' \
        '{body}</div>\n'.format(
            kind=escape(kind),
            cls=' alert-block' if rich else '',
            close='<button type="button" class="close" data-dismiss="alert" '
                  'aria-label="Close"><span aria-hidden="true">×</span>'
                  '</button>' if close else '',
            body=rich or escape(plain),
        )


@nine
class FlashMessage(object):
    ___doc__ = __doc__

    KINDS = {'danger', 'warning', 'info', 'success'}

    def __init__(self, plain=None, rich=None, kind='warning', close=True,
                 allow_duplicate=False):
        assert (plain and not rich) or (rich and not plain)
        if kind == 'error':
            kind = 'danger'
        assert kind in self.KINDS, 'Unknown kind of alert: "{0}". ' \
            "Possible kinds are {1}".format(kind, self.KINDS)
        self.kind = kind
        self.rich = rich
        self.plain = plain
        self.close = close

    def __repr__(self):
        return 'FlashMessage("{0}")'.format(self.plain or self.rich[:40])

    def __str__(self):
        return self.rich or self.plain

    def to_dict(self, whitelist=None):
        """A returns a new dictionary containing all values in this instance.

        ...or the subset indicated in the ``whitelist`` argument.
        """
        if whitelist:
            return {k: v for k, v in self.__dict__.items() if k in whitelist}
        else:
            return copy(self.__dict__)

    @property
    def bootstrap_alert(self):
        return bootstrap_alert(
            self.plain, self.rich, kind=self.kind, close=self.close)
