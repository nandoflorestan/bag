#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''page_deps.py

Copyright © 2011 Nando Florestan
with thanks to Tiago Fassoni and Edgar Alvarenga for valuable feedback.

License: BSD

The problem: script and CSS linking in HTML, using various templates
====================================================================

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

I asked on IRC what other developers thought about this idea, you can read it
at __feedback__ in this module.


My solution: PageDeps
=====================

The following couple of classes are an attempt to solve the described problem.
First of all, while you configure the application, you declare the files
that might be imported:

    deps = DepsRegistry()
    deps.lib('jquery', "/static/scripts/jquery-1.4.2.min.js")
    deps.lib('deform', "/static/scripts/deform.js", depends='jquery')

The first argument to lib() -- and in fact to the other methods, too --
is a simple name for you to refer to the item later on.

As you can see, we can declare that deform.js depends on jquery. For more than
one dependency, you may use a list, tuple or a pipe-separated string:

    depends=('jquery', 'jquery.ui')
    # or
    depends='jquery|jquery.ui'

What about CSS? Maybe there the declaration order will be enough?

    deps.stylesheet('deform1', "/deform/css/form.css")
    deps.stylesheet('deform2', "/deform/css/theme.css")

We keep track of the order the stylesheets are declared in,
and use that order later when outputting your <head> imports.

Actually, if you use, for example, the Deform library, you need to import
javascript files as well as CSS files, so we have a notion of a *package*:

    deps.package('deform', libs='deform', css='deform1|deform2',
                 onload='deform.load();')

We also have a concept of "onload" javascript fragment: a few lines of JS code
that should probably be declared at the bottom of the page --
something "ad hoc" that might use libraries and execute immediately,
as in the example above.

OK, that is all for the registry, done at initialization time.

But web servers are usually threaded and we cannot confuse the needs of
one page being served with another. So now, for each new request,
make sure your web framework instantiates a PageDeps,
passing it the DepsRegistry instance we built above, and make it available to
controllers and templates. For instance, in the Pyramid web framework:

    @subscriber(interfaces.INewRequest)
    def on_new_request(event):
        event.request.page_deps = PageDeps(deps)

After that, controller/view code -- as well as templates, in some more
powerful templating languages -- can easily access the PageDeps instance
and do this kind of thing:

    # Use just one library:
    request.page_deps.lib('jquery')
    # Use 2 or more libraries:
    request.page_deps.libs(('jquery.ui', 'deform'))
    # Use a couple of stylesheets:
    request.page_deps.stylesheets('deform1|deform2')
    # Or maybe import several stylesheets and javascript libraries at once:
    request.page_deps.package('deform')

A file can be requested more than once, but it will appear in the HTML
output only once and in the correct order.

Finally, to get the HTML output, you just include this inside the <head>
element of your master template:

    ${Markup(request.page_deps.out_stylesheets)}
    ${Markup(request.page_deps.out_libs)}
    </head>

...and this at the bottom of the master template, for eventual javascript:

    ${Markup(request.page_deps.out_onloads(tag=True))}
    </body>

Alternatively, you can simply get lists of URLs (already sorted):

    request.page_deps.sorted_stylesheets
    request.page_deps.sorted_libs

...where "Markup" is whatever function your templating language uses to
mark a string as a literal, so it won't be escaped. ("Markup" is from Genshi.)


A caveat
========

You are of course on your own to ensure that the code that outputs the
HTML soup runs *after* all the code that declares requirements for
libs and stylesheets. (How to do so depends on the templating language
being used.)

Therefore, there are 4 moments that should never be confused:

* Declaration of all available libs and stylesheets (and their proper order),
done as the web server starts, with the DepsRegistry class;
* In the scope of one request, instantiation of a PageDeps,
which is made available to the system;
* Declaration of what is needed by the current request (possible in various
places);
* Output.


Deployment profiles
===================

Sometimes you want to use one version of a javascript library in development
(for debugging), but a compressed version in production (for speed).
You might have even more than these 2 deployment scenarios.

For this purpose, you pass your deployment profiles' names, as well as the
currently configured profile, to the DepsRegistry constructor:

    deps = DepsRegistry(profiles='development|cdn|static',
                        profile=settings.get('page_deps.profile', 'cdn'))

The above code declares 3 profiles (development, CDN and static),
and passes as the "profile" argument a string, taken from a configuration file,
corresponding to the currently activated profile (the default being 'cdn').

Now you can pass more than one string as the URL of your libs and stylesheets:

    deps.lib('jquery', ('/static/lib/jquery-1.5.js',
        'https://ajax.googleapis.com/ajax/libs/jquery/1.5.0/jquery.min.js',
        '/static/lib/jquery-1.5.min.js'))

The order of the above URLs corresponds to the order of the declared
deployment profiles, e.g., the first is for development, the second is a CDN,
and the last is static.

Because the order is the same, DepsRegistry knows which URL to actually use.

This way you can declare the libraries once in your code, in a centralized
place, but easily configure which one is used based on
the deployment configuration.


Questions?
==========

For feature requests and bug reports, please visit
https://github.com/it3s/mootiro_web/issues


In time: There is an alternative to this
========================================

After I wrote this module someone showed me Fanstatic:
http://fanstatic.org

Fanstatic solves this problem while being a WSGI middleware.
We have preferred to deal with the problem at the application level.

I haven't tried Fanstatic yet... it seems a little over-engineered...
using Python eggs to describe javascript libraries? My solution is
the simplest thing that works.

But "Fanstatic" is a much more creative name, I envy that :)
'''


# http://docs.python.org/whatsnew/pep-328.html
from __future__ import absolute_import
from __future__ import print_function   # deletes the print statement
from __future__ import unicode_literals # unicode by default

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

try:
    from functools import total_ordering
except ImportError:
    def total_ordering(cls):
        """Class decorator that fills in missing ordering methods.

        http://code.activestate.com/recipes/576685/
        """
        convert = {
            b'__lt__': [(b'__gt__', lambda self, other: other < self),
                       (b'__le__', lambda self, other: not other < self),
                       (b'__ge__', lambda self, other: not self < other)],
            b'__le__': [(b'__ge__', lambda self, other: other <= self),
                       (b'__lt__', lambda self, other: not other <= self),
                       (b'__gt__', lambda self, other: not self <= other)],
            b'__gt__': [(b'__lt__', lambda self, other: other > self),
                       (b'__ge__', lambda self, other: not other > self),
                       (b'__le__', lambda self, other: not self > other)],
            b'__ge__': [(b'__le__', lambda self, other: other >= self),
                       (b'__gt__', lambda self, other: not other >= self),
                       (b'__lt__', lambda self, other: not self >= other)]
        }
        roots = set(dir(cls)) & set(convert)
        if not roots:
            raise ValueError('must define at least one ordering operation: < > <= >=')
        root = max(roots)       # prefer __lt__ to __le__ to __gt__ to __ge__
        for opname, opfunc in convert[root]:
            if opname not in roots:
                opfunc.__name__ = opname
                opfunc.__doc__ = getattr(int, opname).__doc__
                setattr(cls, opname, opfunc)
        return cls


@total_ordering
class Library(object):
    '''Represents a javascript library. Used internally.'''
    def __init__(self, name, url, dependencies=None):
        self.url = url
        self.name = name
        self.dependencies = dependencies

    def __gt__(self, other):
        '''Compare this Library instance to another (for sorting).
        Returns True if this instance is "greater than" the other
        (meaning it should be placed after the other).'''
        return other in self.dependencies

    def __repr__(self):
        '''Useful for debugging in ipython.'''
        return 'Library(name="{0}", url="{1}", dependencies={2})' \
            .format(self.name, self.url,
                    [d.name for d in self.dependencies])


@total_ordering
class Stylesheet(object):
    '''Represents a CSS stylesheet file. Used internally.'''
    def __init__(self, name, url, priority=100):
        self.url = url
        self.name = name
        self.priority = priority

    def __gt__(self, other):
        '''Compare this Stylesheet instance to another (for sorting).
        Returns True if this instance is "greater than" the other
        (meaning it should be placed after the other).'''
        return self.priority > other.priority

    def __repr__(self):
        '''Useful for debugging in ipython.'''
        return '{0}(name="{1}", url="{2}", priority={3})' \
            .format(type(self), self.name, self.url, self.priority)


class DepsRegistry(object):
    '''Should be used at web server initialization time to register every
    javascript and CSS file used by the application.

    The order of registration is important: it must be done bottom-up.

        deps_registry = DepsRegistry()
        deps_registry.lib('jquery', "/static/scripts/jquery-1.4.2.min.js")
        deps_registry.lib('deform', "/static/scripts/deform.js", depends='jquery')

    '''
    SEP = '|'

    def __init__(self,
                 profiles='development|production', profile='development'):
        '''*profiles* is a string containing server profiles separated by
        a pipe |.
        *profile* is the selected profile -- it typically comes from
        a configuration setting.

        Based on *profiles* and *profile* we select which URL to use for each
        javascript library.
        '''
        i = 0
        for s in profiles.split(self.SEP):
            if s == profile:
                self._profile = i
                break
            i += 1
        if not hasattr(self, '_profile'):
            raise RuntimeError('Profile "{0}" not in "{1}".' \
                               .format(profile, profiles))
        self._css = {}
        self._libs = {}
        self._packages = {}
        self._css_priority = 0 # this autoincrements :)

    def lib(self, name, urls, depends=[]):
        '''If provided, the *depends* argument must be either a list of strings,
        or one string separated by pipes: |

        Same can be said of the *urls* parameter.

        If you only provide one url, it is used by all profiles.

        Each of these items must be the name of another library,
        required for this library to work.
        '''
        if hasattr(self._libs, name):
            raise RuntimeError \
                ('Library "{0}" already registered.'.format(name))
        # Recursively list all the dependencies, and
        # swap dependency names with actual Library objects
        deplibs = []
        if isinstance(depends, basestring):
            depends = depends.split(self.SEP)
        if depends:
            for depname in depends:
                self._recursively_add_deps(depname, deplibs)
        if isinstance(urls, basestring):
            urls = urls.split(self.SEP)
        the_url = urls[0] if len(urls) == 1 else urls[self._profile]
        self._libs[name] = Library(name, the_url, deplibs)

    def _recursively_add_deps(self, libname, out_list):
        try:
            lib = self._libs[libname]
        except KeyError:
            raise KeyError('Dependency "{0}" not yet registered.' \
                           .format(libname))
        for dep in lib.dependencies:
            self._recursively_add_deps(dep.name, out_list)
        if lib not in out_list:
            out_list.append(lib)

    def stylesheet(self, name, urls, priority=None):
        '''The *urls* argument must be either a list of strings,
        or one string separated by pipes: |

        If you only provide one url, it is used by all profiles.
        '''
        if isinstance(urls, basestring):
            urls = urls.split(self.SEP)
        self._css_priority += 1
        the_url = urls[0] if len(urls) == 1 else urls[self._profile]
        self._css[name] = Stylesheet(name, the_url,
                                     priority or self._css_priority)

    def package(self, name, libs=[], css=[], onload=''):
        self._packages[name] = (libs, css, onload)


class PageDeps(object):
    '''Represents the dependencies of a page; i.e. CSS stylesheets,
    javascript libraries and javascript onload code.
    Easy to declare and provides the HTML tag soup.
    '''
    def __init__(self, registry):
        self._reg = registry
        self._css = []
        self._libs = []
        self.onloads = []

    def lib(self, name):
        '''Adds a requirement of a javascript library to this page,
        if not already there.
        '''
        lib = self._reg._libs[name]
        if lib not in self._libs:
            self._libs.append(lib)

    def libs(self, names):
        '''Adds requirements for one or more javascript libraries to this page,
        if not already there.
        '''
        if isinstance(names, basestring):
            names = names.split('|')
        for name in names:
            self.lib(name)

    @property
    def sorted_libs(self):
        '''Recommended for use in your templating language. Returns a list of
        the URLs for the javascript libraries required by this page.
        '''
        flat = []
        for lib in self._libs:
            for dep in lib.dependencies:
                if dep.url not in flat:
                    flat.append(dep.url)
            if lib.url not in flat:
                flat.append(lib.url)
        return flat

    @property
    def out_libs(self):
        '''Returns a string containing the script tags.'''
        return '\n'.join(['<script type="text/javascript" src="{0}"></script>' \
            .format(url) for url in self.sorted_libs])

    def stylesheet(self, name):
        '''Adds a requirement of a CSS stylesheet to this page, if not
        already there.
        '''
        css = self._reg._css[name]
        if css not in self._css:
            self._css.append(css)

    def stylesheets(self, names):
        '''Adds requirements for a few CSS stylesheets to this page,
        if not already there.
        '''
        if isinstance(names, basestring):
            names = names.split('|')
        for name in names:
            self.stylesheet(name)

    @property
    def sorted_stylesheets(self):
        '''Recommended for use in your templating language. Returns a list of
        the URLs for the CSS stylesheets required by this page.
        '''
        return [s.url for s in sorted(self._css)]

    @property
    def out_stylesheets(self):
        '''Returns a string containing the CSS link tags.'''
        CSS_TAG = '<link rel="stylesheet" type="text/css" href="{0}" />'
        return '\n'.join([CSS_TAG.format(url) for url in
                          self.sorted_stylesheets])

    def onload(self, code):
        '''Adds some javascript onload code.'''
        self.onloads.append(code)

    def out_onloads(self, tag=False):
        # TODO: If jquery has been requested, maybe we should detect it here
        # and uncomment the following comments.
        if not self.onloads:
            return '\n'
        s = StringIO()
        if tag:
            s.write('<script type="text/javascript">\n')
        #if jquery:
        #    s.write('$(function() {\n')
        for o in self.onloads:
            s.write(o)
            s.write('\n')
        #if jquery:
        #    s.write('});\n')
        if tag:
            s.write('</script>\n')
        return s.getvalue()

    def package(self, name):
        '''Require a package.'''
        libs, css, onload = self._reg._packages[name]
        self.libs(libs)
        self.stylesheets(css)
        if callable(onload):
            self.onload(onload())
        else:
            self.onload(onload)

    def __unicode__(self):
        return '\n'.join([self.out_stylesheets, self.out_libs,
                          self.out_onloads(tag=True)])


'''Tests'''
if __name__ == '__main__':
    r = DepsRegistry()
    r.lib('jquery', ['http://jquery'])
    r.stylesheet('jquery', 'http://jquery.css')
    r.lib('jquery.ui', 'http://jquery.ui', 'jquery')
    r.lib('jquery.ai', 'http://jquery.ai', 'jquery.ui')
    r.lib('deform', 'http://deform.js', 'jquery')
    r.stylesheet('deform', 'http://deform.css')
    r.lib('triform', 'http://triform.js', 'deform|jquery.ui')
    r.package('triform', libs='triform', css='deform')
    print('\n=== Registry ===')
    from pprint import pprint
    pprint(r._libs)
    print('\n=== Page ===')
    p = PageDeps(r)
    p.package('triform')
    p.libs('deform')
    print(p.out_libs)
    p.stylesheets('deform|jquery|deform')
    print(p.out_stylesheets)
    p.onload('// some javascript code here...')
    print(p.out_onloads(tag=True))
    print('\n=== All ===')
    print(unicode(p))


__all__ = ['DepsRegistry', 'PageDeps']


__feedback__ = '''
<nandoflorestan> Does anyone know any code for creating a kind of registry for CSS imports and/or JavaScript imports, and dynamically dealing with their dependencies?
<benbangert> nandoflorestan: not offhand, toscawidgets has some stuff to try and track repeat CSS/JS includes and such
<nandoflorestan> Here is a specification I wrote for such a library:
(...)
<benbangert> nandoflorestan: I guess the reason I shy away from that is its inefficient to have a bunch of CSS/JS links on a page
<benbangert> I usually put all the JS required for the entire site together in one file, minimize the crap out of it, and serve it once with a super long expires
<benbangert> same with CSS
<mgedmin> it would be shiny to have the framework do that for me
<mgedmin> bunch of .js and .css files in my source tree --> automatic collection + minification + caching of minified version on disk + serving with long expiration date and hash/timestamp in url
<rmarianski> some guys worked on some middleware at some point in the past to do that
<rmarianski> http://svn.repoze.org/repoze.squeeze/trunk/
<rmarianski> i'm not sure what the status of that is currently though
<rmarianski> looks like malthe did most of it
<RaFromBRC> :)
<blaflamme> marianski, that middleware looks good

<benbangert> but I know for many uses that just doesn't work
<benbangert> so I definitely see the utility of something like that
<RaFromBRC> nandoflorestan: yeah, i think it looks useful... i've used similar tools in other systems
<gjhiggins> nandoflorestan: headbottom would be useful
<ScottA> nandoflorestan: That looks very useful. Having registry.head_bottom would be semantically nice
<ScottA> Or something to that effect
<nandoflorestan> Why is head_bottom useful if we have dependency checking?
<gjhiggins> nandoflorestan: less work for the dev
<nandoflorestan> just tell me how so, just so I know we are on the same page here
<ScottA> Pure semantics. There's some javascript stuff I like to stick in the head that isn't library code. jQuery(document).ready(), data structures, that sort of thing
<nandoflorestan> ScottA, thanks, I understand it better after what you said.
'''
