# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
    unicode_literals)
from ...six import compat23


@compat23
class FlashMessage(object):
    '''A flash message that renders in Twitter Bootstrap 2.1 style.
    To register a message, simply instantiate it.
    '''
    __slots__ = 'kind text block'.split()
    KINDS = set('error warning info success'.split())

    def __init__(self, request, text, kind='warning', block=False,
            allow_duplicate=True):
        if not kind in self.KINDS:
            raise RuntimeError("Unknown kind of alert: \"{}\". " \
                "Possible kinds are {}".format(kind, self.KINDS))
        self.kind = kind
        self.text = text
        self.block = block
        request.session.flash(self, allow_duplicate=allow_duplicate)

    def __unicode__(self):
        return '<div class="alert alert-{0}{1}"><button type="button" ' \
            'class="close" data-dismiss="alert">×</button>{2}</div>\n' \
            .format(self.kind, ' alert-block' if self.block else '', self.text)


def render_flash_messages(request):
    msgs = request.session.pop_flash()
    return ''.join(msgs)
