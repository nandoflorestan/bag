"""FlashMessage is the natural class to store UI notifications.

Because it knows:

- the content of a flash message in either plain or rich form(s)
- the level (color) of the message, such as info, danger, success etc.
- different ways of rendering the message on the page
- whatever else you want (you can add instance variables or subclass it).

This can be used in any web framework. We provide integration for Pyramid
in the module :mod:`bag.web.pyramid.flash_msg`.

FlashMessage is able to render itself with Bootstrap styles.

If you are not using Bootstrap, or if you don't like that I am
generating HTML in Python, or if you want some additional content or style,
you can still use this class and just render the messages yourself.
You can even override the ``bootstrap_alert`` property in a subclass.

A more useful version of this module is provided by the *state.py*
module of the *kerno* library.
"""

from html import escape
from copy import copy


def bootstrap_alert(plain=None, rich=None, level='warning', close=True, v=3):
    """Render a bootstrap alert message, optionally with a close button.

    Provide either ``plain`` or ``rich`` content. The parameter ``v``
    can be 3 or 2 depending on your bootstrap version (default 3).
    """
    # In bootstrap 3, the old "error" class becomes "danger":
    if level == 'danger' and v == 2:
        level = 'error'

    return '<div class="alert alert-{level}{cls} fade in">{close}' \
        '{body}</div>\n'.format(
            level=escape(level),
            cls=' alert-block' if rich else '',
            close='<button type="button" class="close" data-dismiss="alert" '
                  'aria-label="Close"><span aria-hidden="true">×</span>'
                  '</button>' if close else '',
            body=rich or escape(plain),
        )


class FlashMessage:
    ___doc__ = __doc__

    LEVELS = {'danger', 'warning', 'info', 'success'}

    def __init__(
        self, plain=None, rich=None, level='warning', close=True,
        allow_duplicate=False,
    ):
        assert (plain and not rich) or (rich and not plain)
        if level == 'error':
            level = 'danger'
        assert level in self.LEVELS, 'Unknown alert level: "{0}". ' \
            "Possible levels are {1}".format(level, self.LEVELS)
        self.level = level
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
            self.plain, self.rich, level=self.level, close=self.close)
