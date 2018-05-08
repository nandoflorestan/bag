"""A little plugin supporting human language alternation in Pyramid.

It lets you enable and disable locales (as your translations allow)
in the configuration file.

This module also offers *BaseLocalizedView*, a useful mixin class for
your application's base view.

Enabling the module in 2 steps
------------------------------

1) Add a setting to your .ini file with the locales you want to enable,
such as::

    bag.locale.enable = en pt_BR es de fr

2) Add to your initialization file::

    config.include('bag.web.pyramid.locale')

Effects of enabling this module as described above
--------------------------------------------------

1) A view is registered so the user can, for instance, browse to
/locale/pt_BR
in order to change the locale to Brazilian Portuguese.
This works by setting the locale cookie.

2) To improve the experience of first-time visitors, a locale negotiator
is registered that checks the browser's stated preferred languages
against the "bag.locale.enable" setting in the .ini file.

3) The "bag.locale.enable" setting
is replaced with an OrderedDictionary that is useful
for you to build a user interface for locale choice.

4) In templates, that dictionary is available as *enabled_locales*.

For instance, you might do this in your template to list the
available locales so the user can click and change languages:

.. code-block:: html

    <span class='languages-selector'
        py:with="locales = enabled_locales.values()">
      <py:for each="loc in locales">
        <a href="${url('locale', locale=loc.code)}"
           title="${loc.title}"
           py:strip="locale_code == loc.code"
           py:content="loc.code[:2]" />
        <span py:if="not loc is locales[-1]" class="separator">|</span>
      </py:for>
    </span>

5) In your master template, you can set the 2 lang attributes
on the <html> tag::

    xml:lang="${locale_code[:2]}" lang="${locale_code[:2]}"

...because the variable ``locale_code`` is made available to
template context.
"""

from collections import OrderedDict
from babel import Locale
from babel.numbers import (
    format_number as as_number, format_currency as as_currency)
from pyramid.httpexceptions import HTTPSeeOther
from pyramid.i18n import get_locale_name, default_locale_negotiator
from . import _

SETTING_NAME = 'bag.locale.enable'


class LocaleInfo:

    def __init__(self, code, display_name, english_name, title=None,
                 babel_locale=None):
        self.code = code
        self.display_name = display_name
        self.english_name = english_name
        self.title = title
        self.babel_locale = babel_locale

    def __repr__(self):
        return self.code

    def __str__(self):
        return self.display_name


locale_titles = dict(
    en='Change to English',
    en_US='Change to English - United States',
    en_DEV='Change to strings as in the source code',
    pt='Mudar para português',
    pt_BR='Mudar para português do Brasil',
    es='Cambiar a español',
    de='Auf Deutsch benutzen',
)  # Please help us: send more entries to this dict


class LocaleDict(OrderedDict):
    """A dictionary of dictionaries grouping:

    * locale codes (i.e. "pt_BR"),
    * human-readable and translatable language names such as "English", and
    * titles such as "Change to English", written in THAT language.
    """

    def add(self, code, display_name=None, english_name=None, title=None):
        babel_locale = Locale(*code.split("_"))
        self[code] = LocaleInfo(
            code, title=title or locale_titles.get(code),
            display_name=display_name or babel_locale.display_name,
            english_name=english_name or babel_locale.english_name,
            babel_locale=babel_locale)


def prepare_enabled_locales(settings, Dict=LocaleDict):
    """If you have a *bag.locale.enable* setting with a value such as
    "en pt-BR es fr de" (without the quotes),
    this method substitutes that setting with
    a dictionary of Locale objects which is useful to
    build a web interface for the user to change the locale.
    """
    # Read from settings a list of locale codes that should be enabled
    codes = set(settings.get(SETTING_NAME, 'en').split(' '))
    # Create the LocaleDict containing info for each code
    langs = Dict()
    for code in codes:
        langs.add(code)
    # Replace the setting with the dictionary, containing more information
    settings[SETTING_NAME] = langs
    return langs


def locale_cookie_headers(locale_code):
    """Return HTTP header setting the cookie that stores the Pyramid locale."""
    return [(
        'Set-Cookie',
        '_LOCALE_={0}; expires='
        'Fri, 31-Dec-9999 23:00:00 GMT; Path=/'.format(locale_code))]


def locale_view(request):
    """View that sets the locale cookie -- as long as the requested locale
    is enabled -- and redirects back to the referer.
    """
    locale_code = request.matchdict['locale']
    # Ensure this locale code is one of the enabled_locales
    if locale_code not in request.registry.settings[SETTING_NAME]:
        raise KeyError('Locale not enabled: "{0}"'.format(locale_code))
    return HTTPSeeOther(
        location=request.referrer or '/',
        headers=locale_cookie_headers(locale_code))


def locale_from_browser(request):
    """The browser provides the user's preferred languages, ordered.
    They come in the *Accept-Language* header.

    This function returns the best match between that list and
    the enabled languages.

    Most of the implementation is in the WebOb request object.
    """
    # settings = request.registry.settings
    # enabled_locales = settings[SETTING_NAME].keys()
    # first = enabled_locales[0]
    # return request.accept_language.best_match(enabled_locales,
    #     default_match=settings.get("pyramid.default_locale_name", first))
    return request.accept_language.best_match(
        request.registry.settings[SETTING_NAME].keys())


def locale_negotiator(request):
    """This is a locale negotiator that decorates Pyramid's default one.

    If the default locale negotiator's schemes should fail,
    we try to match the browser's stated preferred languages
    with our configured enabled locales.
    """
    return default_locale_negotiator(request) or locale_from_browser(request)


def add_template_globals(event):
    """Makes the following variables readily available in template context:

    * *enabled_locales*: OrderedDict containing the enabled locales
    """
    event['enabled_locales'] = \
        event['request'].registry.settings[SETTING_NAME]


def includeme(config):
    """Integrate this module into a Pyramid app."""
    if hasattr(config, 'bag_locale_included'):
        return  # Include only once per config
    config.bag_locale_included = True

    prepare_enabled_locales(config.get_settings())
    config.set_locale_negotiator(locale_negotiator)
    config.add_route('locale', 'locale/{locale}')
    config.add_view(locale_view, route_name='locale')
    from pyramid.interfaces import IBeforeRender
    config.add_subscriber(add_template_globals, IBeforeRender)


class BaseLocalizedView:
    """A mixin class for your application's base view class."""

    def format_number(self, n):
        return as_number(n, locale=self.request.locale_name)

    def format_currency(self, n, currency=None, format=None):
        return as_currency(
            n, format=format,
            currency=currency or getattr(self, 'default_currency', 'USD'),
            locale=self.request.locale_name)


def format_currency(request, n, currency='USD', format=None):
    return as_currency(
        n, format=format, currency=currency, locale=request.locale_name)


def sorted_countries(arg, top_entry=True):  # TODO memoized version
    """*arg* may be either the desired locale code or the request object,
    from which the locale will be discovered.

    Returns a list of tuples like ``('BR', 'Brazil')``, already sorted,
    ready for inclusion in your web form.
    """
    code = arg if isinstance(arg, str) else get_locale_name(arg)

    def generator(territories):
        if top_entry:
            yield ('', _("- Choose -"))  # TODO translate somehow
        for tup in territories:
            if len(tup[0]) == 2:  # Keep only countries
                yield tup
    return sorted(generator(Locale(code).territories.items()),
                  key=lambda x: x[1])


# Colander and Deform section
# ===========================

def locale_exists_validator(settings):
    """If you use Deform or even just Colander, you can use this to get a
    validator that you can use on your user preferences form,
    so a user can only choose a locale that is enabled in the system.

    TODO: Test this new implementation when I use colander again...
    """
    from colander import Invalid
    enabled_locales = settings[SETTING_NAME]

    def validator(node, value):
        if value not in enabled_locales:
            raise Invalid(node, _('Please select a language.'))
    return validator


def language_dropdown(settings, title=_('Locale'), name='locale',
                      blank_option_at_top=True):
    """Let the user select a locale from the enabled ones.

    If you use Deform, you can use this to get a SchemaNode for that.
    """
    import colander as c
    import deform as d

    def options():
        if blank_option_at_top:
            yield ('', _('- Choose -'))
        for loc in settings[SETTING_NAME].values():
            yield (loc.code, loc.display_name)
    values = sorted(options(), key=lambda t: _(t[1]))
    return c.SchemaNode(c.Str(), title=title, name=name,
                        validator=locale_exists_validator(settings),
                        widget=d.widget.SelectWidget(values=values))
