# -*- coding: utf-8 -*-
"""A simple navigation menu system for web apps. Example::

    from bag.web.pyramid.nav import Item

    menu = [
        Item('Home', route='home'),
        Item('Support', 'support'),
        Item('Terms and conditions', static='my_app:static/terms.html'),
        Item('Account', 'account', children=[
            Item('Settings', 'settings'),
            Item('Log out', 'logout'),
            ]),
        ]

A simple Kajiki template using the Pure CSS framework:

.. code-block:: html

    <div class="pure-menu pure-menu-open pure-menu-horizontal">
      <a href="#" class="pure-menu-heading">My website</a>
      <ul>
        <li py:for="item in menu" class="${item.css_class(request)}">
          <a href="${item.href(request)}">${item.label}</a>
        </li>
      </ul>
    </div>

Another example template using Mako and bootstrap:

.. code-block:: html

    <ul class="nav nav-pills pull-left">
    % for item in menu:
      % if item.children:
        <li class="dropdown"><a class="dropdown-toggle"
            data-toggle="dropdown">${item.label}
          <b class="caret"></b></a>
          <ul class="dropdown-menu">
            % for subitem in item.children:
              <li class="${subitem.css_class(request)}"><a
                  href="${subitem.href(request)}">${subitem.label}</a></li>
            % endfor
          </ul>
        </li>
      % else:
        <li class="${item.css_class(request)}"><a
            href="${item.href(request)}">${item.label}</a></li>
      % endif
    % endfor
    </ul>
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from warnings import warn


class Item(object):
    """Represents a navigation menu item."""
    # This constant can be overridden in subclasses:
    ACTIVE_ITEM_CSS_CLASS = 'active'

    def __init__(self, label, route=None, static=None, children=None):
        self.label = label
        self.route = route
        self.static = static
        self.children = children

    def href(self, request):
        if self.route:
            try:
                return request.route_path(self.route)
            except KeyError:
                warn('Menu needs an undefined route: ' + self.route)
                return '#'
        if self.static:
            try:
                return request.static_url(self.static)
            except ValueError:
                warn('Menu needs an undefined static route: ' + self.static)
                return '#'
        return '#'

    def css_class(self, request):
        return self.ACTIVE_ITEM_CSS_CLASS if request.path_info == self.href(
            request) else ''
