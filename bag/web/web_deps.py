"""Load only the CSS and the scripts your page really needs.

The problem: script and CSS linking in composite pages
======================================================

If you develop web applications in Python, and if sometimes you compose a page
out of fragments defined in various templates or functions, you may have asked
yourself how to best factor the importing of stylesheets and
javascript libraries. It feels wrong to use a javascript library in a
template that consubstantiates a page fragment while declaring the
<script> imports in another template.

There are 2 sides to this problem.
Worst of all is not declaring a library that is needed, 'cause then your
page does not work. But almost as bad is declaring everything you
might ever need in your master template -- because then, pages that don't need
heavy javascript libraries will be unnecessarily heavy and slow.

A solution is needed that allows you to first register everything you use,
then on each specific template or view declare what you need right there,
and the solution would generate the HTML imports, without repeating them.

We also must keep in mind that the order matters. For instance, jquery.ui
depends on jquery; and CSS has inheritance, so we need to link stylesheets
in the correct order.

The solution should also work with
any web framework and any templating language.

My solution: WebDeps
====================

The following classes solve the described problem.
First of all, while you configure the application, you declare the files
that might be imported:

.. code-block:: python

    deps = WebDeps()
    deps.lib('jquery', url="/static/lib/jquery-1.7.1.min.js")
    deps.lib('deform', url="/static/lib/deform.js",
        deps='jquery, jquery.ui')

The first argument to lib() -- and in fact to the other methods, too --
is a simple name for you to refer to the item later on.

As you can see, we can declare that deform.js depends on jquery and jquery.ui.
For more than one dependency, you just provide a comma-separated string::

    deps='jquery, jquery.ui'

What about CSS stylesheets? Just call css() instead of lib():

.. code-block:: python

    deps.css('jquery.ui', url='/static/css/jquery.ui.css')
    deps.css('deform', url="/deform/css/form.css", deps='jquery.ui')

They, too, can depend on other stylesheets, which are then output first.

Often javascript libraries work together with certain CSS stylesheets.
So we have a notion of a *package*:

.. code-block:: python

    deps.package('deform', libs='deform', css='deform',
         script='alert("Spam!");', deps='another_package')

A package is a special kind of dependency. It can refer to
scripts, stylesheets, other packages, and even contain some javascript code.

The above package declaration allows you to later say
"I need the 'deform' package here', and the system will output
the deform javascript library, CSS stylesheet, all their dependencies, and
some javascript code.

When everything needed by the web application has been declared, you need to
call close() to obtain a class that you will use on your pages::

    PageDeps = deps.close()

This ends initialization time. We are done with the registry.

But web servers are usually threaded and we cannot confuse the needs of
one page being served with another's. So now, for each new request,
make sure your web framework instantiates a PageDeps, and make it available to
controllers and templates. For instance, in the Pyramid web framework:

.. code-block:: python

    def on_new_request(event):
        event.request.deps = PageDeps()
    from pyramid.events import NewRequest
    # "config" below is assumed to be an instance of a
    # pyramid.config.Configurator object
    config.add_subscriber(on_new_request, NewRequest)

After that, controller/view code -- as well as templates, in some more
powerful templating languages -- can easily access a per-request
PageDeps instance and do this kind of thing:

.. code-block:: python

    # Use just one library:
    request.deps.lib('jquery')
    # Use 2 or more libraries:
    request.deps.lib(('jquery.ui, deform'))
    # Use a couple of stylesheets:
    request.deps.css('global, specific')
    # Or maybe import several stylesheets and javascript libraries at once:
    request.deps.package('deform')
    # You can also add ad hoc script fragments:
    request.deps.script('alert("Bruhaha!");')

A file can be requested more than once, but it will appear in the HTML
output only once and in the correct order.

Finally, we must deliver the HTML output. We shall use the best practice of
putting the CSS stylesheets at the top of the page and all the javascript
at the bottom of the page, near </body>. So, in your master template,
firstly include this inside the <head> element::

    ${Markup(request.deps.top_output)}

...where "Markup" is whatever function your templating language uses to
mark a string as a literal, so it won't be escaped.
"Markup" is from Genshi. In Chameleon you would say::

    ${structure: request.deps.top_output}

OR you can say "deps.css.tags" to the same effect: outputting the stylesheets.

Secondly include this just before the </body> tag::

    ${Markup(request.deps.bottom_output)}

Alternatively, use "deps.lib.tags" and "deps.script.tags".

You can also simply get lists of URLs (already sorted)::

    request.deps.css.urls
    request.deps.lib.urls

In short
========

There are 4 moments that should never be confused:

* Declaration of all available libs and stylesheets (and their proper order),
  done as the web server starts, with the WebDeps class;
* In the scope of one request, instantiation of a PageDeps;
* Declaration of what is needed by the current request;
* Output.

Deployment: Alternative URLs
============================

During development, for debugging, I like to use an uncompressed version
of jquery (a javascript library). But in production I like to use a CDN
(Content Delivery Network) for speed. And if the CDN stops working, I like to
have a third compressed version ready on my server.

These are 3 different URLs jquery.js might be served from. web_deps supports
this choice by letting you declare any and all URLs,
then letting you choose one in your configuration file.

How do you declare more than one URL? Well, the system stores any
keyword arguments you pass to lib() and css():

.. code-block:: python

    deps.lib('jquery', prod="/static/lib/jquery-1.7.1.min.js",
        dev="/static/lib/jquery-1.7.1.js",
        cdn='http://google.com/some/address/jquery-1.7.1.min.js')

Now the system has 3 URLs to choose from. Which will be in effect? Well, you
also provide a callable, that returns the desired URL, to the
WebDeps constructor as a "url_provider" keyword argument.
Its default implementation is this::

    url_provider=lambda resource: resource.url

Evidently the above implementation gets the URL from the "url" argument.
But that could be "dev", "prod", "cdn" or whatever you like.
It is trivial for you to put this decision in a configuration file.
Suppose the configuration file says::

    web_deps.url_choice = cdn

All you have to do is:

.. code-block:: python

    # Read the string from the configuration file, providing a default
    choice = settings.get('web_deps.url_choice', 'prod')
    # Pass a url_provider callable to the WebDeps constructor
    def url_provider(resource):
        return getattr(resource, choice, None) or resource.url
    deps = WebDeps(url_provider=url_provider)

This way you can declare the libraries once in your code, in a centralized
place, but easily configure which one is actually used based on
the deployment configuration.

The above implementation will look for a 'prod' argument if the currently
configured choice is 'prod'. If not found, it will look for a 'url' argument.
This lets you provide either the 3 alternative URLs, or just one.

Why would you provide only one URL? Not every file is provided by a CDN and
not every javascript library is worth compressing. The reality we have
experienced is we either want 3 alternative URLs, or just one. Anyway,
suit yourself in your own url_provider implementation.

Advantages over page_deps
=========================

This module, "web_deps", is superior to my previous attempt, called
"page_deps", in the following ways:

* Dependency declarations may be done in any order.
  You can declare that *b* depends on "a", then declare what "a" is later.
* Some computation occurs when close() is called. From this moment on,
  trying to add a dependency throws an exception.
* The general dependency problem has been solved in the base classes
  Dependency and DepsRegistry, which can be reused in other scenarios.
  The specific web problem is solved by inheriting from these superclasses.
* Therefore, more code is reused between javascript and CSS dependencies.
* Now packages can depend on other packages, too.
* In page_deps stylesheets didn't really have dependencies, just priority.
  This was a mistake.
* Results are cached so your web application runs faster.
* Much better user API.
* The code is better organized.
* It has more comprehensive unit tests.
"""

from ..memoize import memoize
from ..text import uncommafy


def uniquefy(seq, id_fun=lambda x: x):
    """Return a list of unique items in ``seq`` while preserving the order.

    Why? set(seq) might be more expensive and does not preserve the order.
    """
    seen = {}
    result = []
    for item in seq:
        marker = id_fun(item)
        if marker in seen:
            continue
        seen[marker] = 1
        result.append(item)
    return result


class Dependency:
    """Represents a dependency.

    You can store whatever attributes you like by providing keyword
    arguments. The only required argument is a name for this dependency.
    """

    def __init__(self, handle, deps='', **kw):
        assert isinstance(handle, str)
        self.handle = handle
        self.dep_handles = list(uncommafy(deps))
        self.deps = None  # This is only computed on close()
        for k, v in kw.items():
            setattr(self, k, v)

    def __repr__(self):
        return '{0}("{1}")'.format(self.__class__.__name__, self.handle)

    def __str__(self):
        return self.handle

    def recursive_deps(self):
        """Return a deep list of the dependencies, with self as 1st item.

        May contain duplicates.
        """
        flat = [self]
        for dep in self.deps:
            flat.extend(dep.recursive_deps())
        return flat


class DepsRegistry(object):

    def __init__(self):
        self.items = {}

    def admit(self, *deps):
        """The arguments must be Dependency instances."""
        for dep in deps:
            if dep.handle in self.items:
                raise KeyError('{0} already registered.'.format(dep.handle))
            self.items[dep.handle] = dep

    def close(self):
        # Find every actual dependency object from declared handle strings
        for item in self.items.values():
            item.deps = \
                uniquefy([self.items[d] for d in item.dep_handles])
                # , id_fun=lambda d: d.handle)
        # Do not allow admit() to work anymore

        def admit(dep):
            raise RuntimeError(
                'Cannot admit() because registry is already closed.')
        self.admit = admit

    @memoize(100, keymaker=lambda self, items: repr((self, items)))
    def summon(self, items):
        """The parameter `items` can be either a comma-delimited string of
        dependency names, or a list of actual Dependency objects.

        Returns a list of dependency objects,
        plus their dependencies, in the correct order.

        How is it done? A flat list of dependencies is created leaf-to-root,
        then reversed and uniquefied.

        This method can only be called after close().
        """
        flat = []
        if isinstance(items, str):
            items = (self.items[h] for h in uncommafy(items))
        for item in items:
            flat.extend(item.recursive_deps())
        return uniquefy(reversed(flat))


class CallableRegistry(DepsRegistry):
    """Registry that instantiates a dependency when called."""

    item_class = Dependency

    def __call__(self, handle, deps='', **kw):
        """Convenience: add a Dependency without explicitly instantiating it.

        If provided, the *deps* argument must be either a list of strings,
        or one string separated by commas.

        Each of these items must be the name of another resource,
        required for this resource to work.
        """
        self.admit(self.item_class(handle, deps, **kw))


class WebDepsRegistry(CallableRegistry):

    def __init__(self, url_provider, tag_format):
        super(WebDepsRegistry, self).__init__()
        self.url_provider = url_provider
        self.tag_format = tag_format

    @memoize(100, keymaker=lambda self, items: repr((self, items)))
    def urls(self, items):
        """Recommended for use in your templating language. Returns a list of
        the URLs for the dependencies required by this page.
        """
        return [self.url_provider(o) for o in self.summon(items)]

    @memoize(100, keymaker=lambda self, items: repr((self, items)))
    def tags(self, items):
        """Returns a string containing the HTML script tags."""
        return '\n'.join([self.tag_format.format(url)
                          for url in self.urls(items)])


class WebDeps(object):
    """Should be used at web server initialization time to register every
    javascript and CSS file used by the application. Example:

    .. code-block:: python

        deps = WebDeps()
        deps.lib('jquery', url="/static/lib/jquery-1.7.1.min.js")
        deps.lib('deform', url="/static/lib/deform.js",
            deps='jquery, jquery.ui')
        deps.css('deform', url="/deform/css/form.css")
        deps.package('deform', libs='deform', css='deform',
             script='alert("Spam!")')
        PageDeps = deps.close()

    Then in each request you should instantiate the returned PageDeps.
    """

    def __init__(self, url_provider=lambda resource: resource.url):
        """By default, the system will output URLs by looking into the "url"
        instance variable of resources. If needed, you can change this
        by providing a `url_provider` function here.
        """
        self.lib = WebDepsRegistry(
            url_provider=url_provider,
            tag_format='<script type="text/javascript" src="{0}"></script>')
        self.css = WebDepsRegistry(
            url_provider=url_provider,
            tag_format='<link rel="stylesheet" type="text/css" href="{0}" />')
        self.package = CallableRegistry()
        self._url_provider = url_provider

    def close(self):
        """Finishes registration time and returns a factory that
        should be called for each request.
        """
        self.lib.close()
        self.css.close()
        self.package.close()

        def factory():
            return PageDeps(self.lib, self.css, self.package)
        return factory


class PageDepsComponent(object):

    def __init__(self, registry):
        self._items = []
        self.registry = registry

    def __call__(self, handles):
        """Adds one or more requirements to this page or request."""
        for handle in uncommafy(handles):
            self._items.append(self.registry.items[handle])

    @property
    def sorted(self):
        """Returns a list of dependency objects required by this page."""
        return self.registry.summon(self._items)

    @property
    def urls(self):
        """Recommended for use in your templating language. Returns a list of
        the URLs for the dependencies required by this page.
        """
        return self.registry.urls(self._items)

    @property
    def tags(self):
        """Returns a string containing the HTML script tags."""
        return self.registry.tags(self._items)


class ScriptComponent(list):

    def __call__(self, script):  # Included just to keep a common API
        if not script in self:
            self.append(script)

    def output(self, tag=True):
        if not self:
            return '\n'
        s = []
        if tag:
            s.append('<script type="text/javascript">')
        for o in self:
            s.append(o)
        if tag:
            s.append('</script>\n')
        return '\n'.join(s)

    @property
    def tags(self):  # Included just to keep a common API
        return self.output()


class PackageComponent(object):
    """A package is a special kind of dependency. It can refer to
    scripts, stylesheets, other packages, and even contain some
    javascript code.

    During application initialization you can define a package like this::

        deps.package('deform', libs='deform', css='deform',
             script='alert("Spam!");', deps='another_package')

    Later - in a request - you can require all the package elements at once::

        deps.package('deform')
    """

    def __init__(self, packages, deps):
        self._packages = packages
        self._deps = deps

    def __call__(self, handles):
        """Add one or more package requirements to this page or request."""
        if isinstance(handles, str):
            handles = uncommafy(handles)
        for handle in handles:
            package = self._packages.items[handle]
            if hasattr(package, 'deps'):
                self([d.handle for d in package.deps])
            if hasattr(package, 'libs'):
                self._deps.lib(package.libs)
            if hasattr(package, 'css'):
                self._deps.css(package.css)
            if hasattr(package, 'script'):
                self._deps.script(package.script)


class PageDeps:
    """Represents the dependencies of a page.

    An instance must be used on each request.
    Makes it easy to declare dependencies and provides the HTML tag soup.
    """

    def __init__(self, libs, styles, packages):
        """The constructor is called by
        the factory returned by WebDeps.close(), not by you.
        It just assembles a composite object.
        """
        self.lib = PageDepsComponent(libs)
        self.css = PageDepsComponent(styles)
        self.script = ScriptComponent()
        self.package = PackageComponent(packages, self)

    @property
    def top_output(self):
        return self.css.tags

    @property
    def bottom_output(self):
        return self.lib.tags + '\n' + self.script.tags

    def __str__(self):
        return '\n'.join([self.css.tags, self.lib.tags, self.script.tags])

    def light_accordion(self, selector='.accordion', h_tag='h3'):
        """Implements an accordion that depends on jquery only, not jquery.ui.

        The CSS you need is::

            .accordion > h3 { cursor: pointer; }

        The HTML should have this structure:

        .. code-block:: html

            <div class="accordion">
              <h3>Question 1</h3>
              <div class='show'>Answer 1</div>
              <h3>Question 2</h3>
              <div>Answer 2</div>
            </div>

        Use "class='show'" to make some answers initially appear.
        """
        self.lib('jquery')
        s = """
function processAccordion(first) {
  var toHide = $('selector > div').not('.show');
  var toShow = $('selector > div.show');
  if (first) {
    toHide.hide();
    toShow.show();
  } else {
    toHide.slideUp('slow');
    toShow.slideDown('slow');
  }
}
$(function() {
  processAccordion(true);
  $('selector > h_tag').click(function(e) {
    $('selector > div').removeClass('show');
    $(this).next().addClass('show');
    processAccordion();
  });
});""".replace('selector', selector).replace('h_tag', h_tag)
        self.script(s)

    favicon_props = dict(
        ie=dict(
            rel='shortcut icon',
            typ='type="image/x-icon"',
            url='/static/favicon.ico',
            sizes="32x32"),
        normal=dict(
            rel='icon',
            typ='',
            url='/static/favicon32.gif',
            sizes="32x32"),
    )

    def is_ie(self, request):
        """Return True if the browser is Internet Explorer.

        Written for the Pyramid web framework. If you are using another
        framework, you can override this method.
        """
        return request.headers.get("User-Agent", '').find("MSIE") != -1

    def favicon_tag(self, request):
        """Returns the HTML tag for the favicon. If the browser is IE,
        a different tag is returned. You can configure either tag by
        changing the PageDeps.favicon_props dictionary.
        """
        s = '<link rel="{rel}" {typ} href="{url}" sizes="{sizes}" />'.format(
            **self.favicon_props['ie' if self.is_ie(request) else 'normal'])
        return s
