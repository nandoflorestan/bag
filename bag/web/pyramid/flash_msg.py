# -*- coding: utf-8 -*-

'''Advanced flash messages scheme for Pyramid.

Many people use the queues of flash messages to separate them by their level
(error, warning, info or success) in code such as this::

    request.session.flash(str(e), 'error')

The problem with this is that messages won't appear in the order in which
they were created. Because each queue is processed separately in the
template, order is lost and messages are grouped by kind.

Our solution: we store the level *with* the message, so you can create your
flash messages as bootstrap alerts *in a single queue* like this::

    from bag.web.pyramid.flash_msg import FlashMessage
    FlashMessage(request,
        "You can enqueue a message simply by instantiating a FlashMessage.",
        kind='warning')

An additional feature is available if you add this to your app initialization::

    config.include('bag.web.pyramid.flash_msg')

Then you can simply do, in templates:

    ${request.render_flash_messages()}

...to render the messages with Bootstrap styling.

If you don't like that I am generating HTML in Python, or if you just
want some additional styling, then you can just loop over the flash messages
in your template (now you only need one queue) and use
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

    We put ``render_flash_messages()`` in the request, not in some base view;
    this way, overridden templates can use it, too.

    If you want to use the queues feature (not recommended), add this
    configuration setting:

        bag.flash.use_queues = true
    '''
    global included
    if included:
        return
    from pyramid.settings import asbool
    use_queues = config.registry.settings.get('bag.flash.use_queues', False)
    fn = render_flash_messages_from_queues if asbool(use_queues) \
        else render_flash_messages

    from pkg_resources import get_distribution
    if get_distribution('pyramid').version.startswith('1.3'):
        config.set_request_property(fn, name=str('render_flash_messages'))
        # str() call above is because Pyramid demands the native string type.
    else:  # In Pyramid 1.4 and beyond, use *add_request_method*
        config.add_request_method(callable=fn,
            name=str('render_flash_messages'))
    included = True
included = False
