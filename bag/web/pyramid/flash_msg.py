# -*- coding: utf-8 -*-

'''Advanced flash messages scheme for Pyramid.

    from bag.web.pyramid.flash_msg import FlashMessage
    FlashMessage(request,
        "You can enqueue a message simply by instantiating a FlashMessage.",
        kind='warning')

    # At app initialization:
    config.include('bag.web.pyramid.flash_msg')
    # This allows you to do, in templates:
    # ${request.render_flash_messages()}
    # ...and the messages will appear with Bootstrap styling.
'''

from __future__ import (absolute_import, division, print_function,
    unicode_literals)
from cgi import escape
from ...six import compat23, unicode


def bootstrap_msg(text, kind='warning', block=False):
    return '<div class="alert alert-{0}{1}"><button type="button" ' \
        'class="close" data-dismiss="alert">×</button>{2}</div>\n' \
        .format(escape(kind), ' alert-block' if block else '', escape(text))


@compat23
class FlashMessage(object):
    '''A flash message that renders in Twitter Bootstrap 2.1 style.
    To register a message, simply instantiate it.
    '''
    __slots__ = 'kind text block'.split()
    KINDS = set(['error', 'warning', 'info', 'success'])

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
    return ''.join([unicode(m) if isinstance(m, FlashMessage) \
        else bootstrap_msg(m) for m in msgs])


def render_flash_messages_from_queues(request):
    '''This method is for compatibility with other systems only.
    Some developers are using queues named after bootstrap message flavours.
    I think my system (using only the default queue '') is better,
    because FlashMessage already supports a ``kind`` attribute,
    but this function provides a way to display their flash messages, too.

    You can set QUEUES to something else if you like, from user code.
    '''
    msgs = []
    for q in QUEUES:
        for m  in request.session.pop_flash(q):
            html = unicode(m) if isinstance(m, FlashMessage) \
                else bootstrap_msg(m, q)
            msgs.append(html)
    return ''.join(msgs)

QUEUES = set(['error', 'warning', 'info', 'success', ''])


def includeme(config):
    '''Make the request object capable of rendering the flash messages.

    Better to have this in the request, not in the views;
    this way, overridden templates can use it, too.
    '''
    config.add_request_method(callable=render_flash_messages_from_queues,
        name='render_flash_messages')
