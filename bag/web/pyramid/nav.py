"""A simple navigation menu system for web apps.

The menu structure can be defined in advance, before any http requests come.
Example::

    from bag.web.pyramid.nav import NavEntry, Route, Static

    menu = [
        NavEntry('Home', url=Route('home')),
        NavEntry('Support', url=Route('support')),
        NavEntry('Terms and conditions',
                 url=Static('my_app:static/terms.html')),
        NavEntry('Account', children=[
            NavEntry('Settings', url=Route('settings')),
            NavEntry('Log out', url=Route('logout')),
        ]),
        NavEntry('What the world is saying about us',
                 url='https://www.google.com/search?q=about+us')
    ]

A Kajiki template using the Pure CSS framework, without submenus:

.. code-block:: html

    <div class="pure-menu pure-menu-open pure-menu-horizontal">
      <a href="#" class="pure-menu-heading">My website</a>
      <ul>
        <li py:for="item in menu" class="${item.css_class(request)}">
          <a href="${item.href(request)}">${item.label}</a>
        </li>
      </ul>
    </div>

Another example template using Mako and Bootstrap 3:

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


class Route:
    """A link that is defined by a Pyramid route name."""

    def __init__(self, route_name):
        """Instantiate."""
        self.url = route_name

    def href(self, request):
        """Return the route_path() of this instance."""
        return request.route_path(self.url)


class Static:
    """A link that is defined by a Pyramid static URL spec."""

    def __init__(self, static_url):
        """Instantiate."""
        self.url = static_url

    def href(self, request):
        """Return the static_url() of this instance."""
        return request.static_url(self.url)


class NavEntry:
    """Represents a navigation menu item, possibly with children."""

    # This constant can be overridden in subclasses:
    ACTIVE_ITEM_CSS_CLASS = 'active'

    def __init__(
        self, label=None, img=None, icon=None, tooltip=None, url='##',
        children=None, **kw
    ):
        """Instantiate, without depending on a request yet.

        The param *url* can be:

        - a ``Route`` instance,
        - a ``Static`` instance,
        - or a string to be output directly.
        """
        assert label or img, "Need either a label or an img"
        self.label = label
        self.img = img  # usually for a logo in the navbar
        self.icon = icon
        self.tooltip = tooltip
        self.url = url
        self.children = children if children else []
        self.__dict__.update(kw)

    def href(self, value, request):
        """Compute the link previously planned in this instance."""
        if value is None:
            return None
        elif isinstance(value, str):
            return value
        else:
            return value.href(request)

    def css_class(self, request):
        """Return "active" if this NavEntry corresponds to the current URL."""
        return self.ACTIVE_ITEM_CSS_CLASS if request.path_info == self.href(
            self.url, request).split('#')[0] else ''

    def __repr__(self):
        return '<NavEntry: {}>'.format(self.label or self.img)

    def to_dict(self, request):
        """Convert this instance into a dict, usually for JSON output."""
        adict = self.__dict__.copy()
        adict['url'] = self.href(adict['url'], request)
        adict['img'] = self.href(adict['img'], request)
        if self.children:
            adict['children'] = [
                child.to_dict(request) for child in self.children]
        return adict
