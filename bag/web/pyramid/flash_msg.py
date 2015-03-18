# -*- coding: utf-8 -*-

'''Advanced flash messages scheme for Pyramid.

    Some developers have been using the queues of flash messages to separate
    them by level (danger, warning, info or success) in code such as this::

        request.session.flash(str(e), 'danger')

    The problem with this is that messages won't appear in the order in which
    they were created. Because each queue is processed separately in the
    template, order is lost and messages are grouped by kind.

    Our solution: we store the level *with* the message, so you can create
    flash messages as bootstrap alerts *in a single queue* like this::

        from bag.web.pyramid.flash_msg import FlashMessage
        FlashMessage(
            request,
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
from nine import nine, basestring


def bootstrap_alert(plain=None, rich=None, kind='warning', close=True, v=3):
    '''Renders a bootstrap alert message, optionally with a close button.
        Provide either ``plain`` or ``rich`` content. The parameter ``v``
        can be 3 or 2 depending on your bootstrap version (default 3).
        '''
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
    '''A flash message that renders in Twitter Bootstrap style.
    To register a message, simply instantiate it.
    '''
    __slots__ = ('kind', 'plain', 'rich', 'close')

    def __getstate__(self):
        '''Because we are using __slots__, pickling needs this method.'''
        return {i: getattr(self, i) for i in self.__slots__}

    def __setstate__(self, state):
        '''Because we are using __slots__, unpickling needs this method.'''
        for s in self.__slots__:
            setattr(self, s, state.get(s))

    KINDS = set(['danger', 'warning', 'info', 'success'])

    def __init__(self, request, plain=None, rich=None, kind='warning',
                 close=True, allow_duplicate=False):
        assert (plain and not rich) or (rich and not plain)
        if kind == 'error':
            kind = 'danger'
        assert kind in self.KINDS, 'Unknown kind of alert: "{0}". ' \
            "Possible kinds are {1}".format(kind, self.KINDS)
        self.kind = kind
        self.rich = rich
        self.plain = plain
        self.close = close
        request.session.flash(self, allow_duplicate=allow_duplicate)

    def __repr__(self):
        return 'FlashMessage("{0}")'.format(self.plain)

    def __str__(self):
        return self.rich or self.plain

    @property
    def html(self):
        return bootstrap_alert(
            self.plain, self.rich, kind=self.kind, close=self.close)


def render_flash_messages(request):
    msgs = request.session.pop_flash()  # Pops from the '' queue
    return ''.join((bootstrap_alert(m) if isinstance(m, basestring) else m.html
                    for m in msgs))


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
        for m in request.session.pop_flash(q):
            html = m.html if isinstance(m, FlashMessage) \
                else bootstrap_alert(m, q)
            msgs.append(html)
    return ''.join(msgs)

QUEUES = set(['error', 'warning', 'info', 'success', ''])


def includeme(config):
    '''Make a render_flash_messages() function available to every template.

    If you want to use the queues feature (not recommended), add this
    configuration setting:

        bag.flash.use_queues = true
    '''
    if hasattr(config, 'bag_flash_msg_included'):
        return  # Include only once per config
    config.bag_flash_msg_included = True

    from pyramid.events import BeforeRender
    from pyramid.settings import asbool
    use_queues = config.registry.settings.get('bag.flash.use_queues', False)
    fn = render_flash_messages_from_queues if asbool(use_queues) \
        else render_flash_messages

    def on_before_render(event):
        event['render_flash_messages'] = lambda: fn(event['request'])

    config.add_subscriber(on_before_render, BeforeRender)
