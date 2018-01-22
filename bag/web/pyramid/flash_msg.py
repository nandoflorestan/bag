# -*- coding: utf-8 -*-

"""Advanced flash messages scheme for Pyramid.

    This module integrates :py:mod:`bag.web.flash_msg` into Pyramid.
    (That module can be used with any web framework.)

    Why?
    ====

    It is natural to have a single class that knows:

    - the content of a flash message in either plain or rich form(s)
    - the kind (color) of the message, such as info, danger, success etc.
    - different ways of rendering the message on the page
    - whatever else you want.

    The queue problem
    =================

    Some Pyramid applications have used flash message queues to separate
    them by level (danger, warning, info or success) in code such as this::

        request.session.flash(str(e), 'danger')

    The problem with this is that messages won't appear in the order in which
    they were created. Because each queue is processed separately in the
    template, order is lost and messages are grouped by kind.
    This is undesirable and confusing to the user.

    Our solution stores the level *with* the message, so you can add all
    messages to the default queue and process only that queue in templates.

    Installation
    ============

    At web server startup time, add this simple line::

        config.include('bag.web.pyramid.flash_msg')

    Usage
    =====

    Add messages to the queue like this::

        request.add_flash(
            plain="Your password has been changed, thanks.",
            kind='warning',
            close=False,  # user will NOT see an X button to close the alert
            allow_duplicate=False,  # do not bother the user with repeated text
            )

    Then you can simply do, in templates:

        ${render_flash_messages()}

    ...to render the messages with Bootstrap styling.
    The Jinja2 version is ``{{ render_flash_messages() | safe }}``.

    If you don't like the result in any way, just loop over the flash messages
    yourself and do what you want -- no need to use this feature.
    """

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from nine import nine, basestring
from bag.web.flash_msg import FlashMessage, bootstrap_alert


def add_flash(request, allow_duplicate=False, **kw):
    """Convenience function that adds a flash message to the user's session."""
    msg = FlashMessage(**kw)
    request.session.flash(msg, allow_duplicate=allow_duplicate)


def render_flash_messages(request):
    msgs = request.session.pop_flash()  # Pops from the '' queue
    return ''.join((
        bootstrap_alert(m) if isinstance(m, basestring)
        else m.bootstrap_alert for m in msgs))


def render_flash_messages_from_queues(request):
    """This method is for compatibility with other systems only.
    Some developers are using queues named after bootstrap message flavours.
    I think my system (using only the default queue '') is better,
    because FlashMessage already supports a ``kind`` attribute,
    but this function provides a way to display their flash messages, too.

    You can set QUEUES to something else if you like, from user code.
    """
    msgs = []
    for q in QUEUES:
        for m in request.session.pop_flash(q):
            html = m.bootstrap_alert if isinstance(m, FlashMessage) \
                else bootstrap_alert(m, q)
            msgs.append(html)
    return ''.join(msgs)

QUEUES = set(['error', 'warning', 'info', 'success', ''])


def make_templates_able_to_render_flash_msgs(config):
    """Make a render_flash_messages() function available to every template.

    If you want to use the queues feature (not recommended), add this
    configuration setting:

        bag.flash.use_queues = true
    """
    if hasattr(config, 'bag_flash_msg_included'):
        return  # Include only once per config
    config.bag_flash_msg_included = True

    from pyramid.events import BeforeRender
    from bag.settings import asbool
    use_queues = config.registry.settings.get('bag.flash.use_queues', False)
    fn = render_flash_messages_from_queues if asbool(use_queues) \
        else render_flash_messages

    def on_before_render(event):
        event['render_flash_messages'] = lambda: fn(event['request'])

    config.add_subscriber(on_before_render, BeforeRender)


def includeme(config):
    config.add_request_method(add_flash, 'add_flash')
    make_templates_able_to_render_flash_msgs(config)
