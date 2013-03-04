# -*- coding: utf-8 -*-

'''Advanced flash messages scheme for Pyramid.

    Many people use the queues of flash messages to separate them by level
    (error, warning, info or success) in code such as this::

        request.session.flash(str(e), 'error')

    The problem with this is that messages won't appear in the order in which
    they were created. Because each queue is processed separately in the
    template, order is lost and messages are grouped by kind.

    Our solution: we store the level *with* the message, so you can create
    flash messages as bootstrap alerts *in a single queue* like this::

        from bag.web.pyramid.flash_msg import FlashMessage
        FlashMessage(request,
            "You can enqueue a message simply by instantiating FlashMessage.",
            kind='warning')

    An additional feature is available if you do this at configuration time::

        config.include('bag.web.pyramid.flash_msg')

    Then you can simply do, in templates:

        ${render_flash_messages()}

    ...to render the messages with Bootstrap styling.

    If you don't like that I am generating HTML in Python, or if you want
    some additional content or style, then you can just loop over the
    flash messages in your template (now you only need one queue) and use
    FlashMessage's instance variables to render the
    bootstrap alerts just the way you want them.
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
        assert kind in self.KINDS, "Unknown kind of alert: \"{}\". " \
                "Possible kinds are {}".format(kind, self.KINDS)
        self.kind = kind
        self.text = text
        self.block = block
        request.session.flash(self, allow_duplicate=allow_duplicate)

    def __repr__(self):
        return 'FlashMessage(req, "{}", kind="{}")'.format(
            self.text, self.kind)

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
    '''Make a render_flash_messages() function available to every template.

    If you want to use the queues feature (not recommended), add this
    configuration setting:

        bag.flash.use_queues = true
    '''
    global included
    if included:
        return

    from pyramid.events import BeforeRender
    from pyramid.settings import asbool
    use_queues = config.registry.settings.get('bag.flash.use_queues', False)
    fn = render_flash_messages_from_queues if asbool(use_queues) \
        else render_flash_messages

    def on_before_render(event):
        event['render_flash_messages'] = lambda: fn(event['request'])

    config.add_subscriber(on_before_render, BeforeRender)
    included = True
included = False
