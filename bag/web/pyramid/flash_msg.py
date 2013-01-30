# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
    unicode_literals)
from ...six import compat23, unicode


def bootstrap_msg(text, kind='warning', block=False):
    return '<div class="alert alert-{0}{1}"><button type="button" ' \
        'class="close" data-dismiss="alert">×</button>{2}</div>\n' \
        .format(kind, ' alert-block' if block else '', text)


@compat23
class FlashMessage(object):
    '''A flash message that renders in Twitter Bootstrap 2.1 style.
    To register a message, simply instantiate it.
    '''
    __slots__ = 'kind text block'.split()
    KINDS = set('error warning info success'.split())

    def __init__(self, request, text, kind='warning', block=False,
            allow_duplicate=False):
        '''*block* should be True for multiline text.'''
        if not kind in self.KINDS:
            raise RuntimeError("Unknown kind of alert: \"{}\". " \
                "Possible kinds are {}".format(kind, self.KINDS))
        self.kind = kind
        self.text = text
        self.block = block
        request.session.flash(self, kind, allow_duplicate=allow_duplicate)

    def __unicode__(self):
        return bootstrap_msg(self.text, self.kind, self.block)


def render_flash_messages(request):
    msgs = request.session.pop_flash()  # Pops from the empty string queue
    return ''.join([unicode(m) for m in msgs])


# Below is code for compatibility with other systems only.


def render_flash_messages_from_queues(request, queues=(
    'error', 'warning', 'info', 'success', '')):
    '''Some people are using queues named after bootstrap message flavours.
    I think my system (using only the default queue '') is better,
    but this function provides a way to display their flash messages, too.
    '''
    msgs = []
    for q in queues:
        for m  in request.session.pop_flash(q):
            msgs.append(bootstrap_msg(m, q))
    return ''.join(msgs)
