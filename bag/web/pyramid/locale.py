#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''A little plugin supporting human language alternation in Pyramid.
It lets you enable and disable locales (as your translations allow)
in the configuration file.

To enable it, there are 2 steps.

1) Add a setting to your .ini file with the locales you want to enable, such as:

    bag.locale.enable = en pt_BR es de fr

2) Add to your initialization file:

    config.include('bag.web.pyramid.locale')

The above line registers a view so you can, for instance, browse to
/locale/pt_BR
in order to change the locale to Brazilian Portuguese.

Also, you will find that the "bag.locale.enable" setting is replaced with
an OrderedDictionary that is useful for you to build a user interface
for locale choice. In templates the dictionary is accessed as *enabled_locales*.

For instance, you might do this in your template to list the
available locales so the user can click and change languages:

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

In your master template, you can set the 2 lang attributes on the <html> tag:

    xml:lang="${locale_code[:2]}" lang="${locale_code[:2]}"

...because the variable "locale_code" is made available to template context.
'''

from __future__ import absolute_import
from __future__ import unicode_literals  # unicode by default
from collections import OrderedDict
from pyramid.httpexceptions import HTTPFound
from pyramid.i18n import get_locale_name
from . import _

SETTING_NAME = 'bag.locale.enable'


class Locale(object):
    def __init__(self, code, name, title):
        self.code = code
        self.name = name
        self.title = title

    def __repr__(self):
        return self.code

    def __unicode__(self):
        return self.name


class LocaleDict(OrderedDict):
    '''A dictionary of dictionaries grouping:

    * locale codes (i.e. "pt_BR"),
    * human-readable and translatable language names such as "English", and
    * titles such as "Change to English".
    '''
    def add(self, code, name, title):
        self[code] = Locale(code, name, title)

    def populate(self):
        '''To add locales, update this method :)'''
        add = self.add
        add('en', _('English'), 'Change to English')
        add('en_DEV', _('Strings as in the code'), 'Change to developer slang')
        add('pt_BR', _('Brazilian Portuguese'), 'Mudar para português')
        add('es', _('Spanish'), 'Cambiar a español')
        add('de', _('German'), 'Auf Deutsch benutzen')
        return self


locales = LocaleDict().populate()


def prepare_enabled_locales(settings, Dict=LocaleDict):
    '''If you have a *bag.locale.enable* setting with a value such as
    "en pt-BR es fr de" (without the quotes),
    this method substitutes that setting with
    a dictionary of Locale objects which is useful to
    build a web interface for the user to change the locale.
    '''
    # Read from settings a list of locale codes that should be enabled
    codes = set(settings.get(SETTING_NAME, 'en').split(' '))
    # Apply the "codes" filter on the supported locales
    langs = Dict()
    for code in codes:
        langs[code] = locales[code]
    # Replace the setting with the dictionary, containing more information
    settings[SETTING_NAME] = langs
    return langs


def locale_cookie_headers(locale_code):
    '''Returns HTTP headers setting the cookie that sets the Pyramid locale.'''
    return [(b'Set-Cookie',
        b'_LOCALE_={0}; expires=Fri, 31-Dec-9999 23:00:00 GMT; Path=/' \
        .format(locale_code.encode('utf8')))]


def locale_view(request):
    '''View that sets the locale cookie -- as long as the requested locale
    is enabled -- and redirects back to the referer.
    '''
    locale_code = request.matchdict['locale']
    # Ensure this locale code is one of the enabled_locales
    if not locale_code in request.registry.settings[SETTING_NAME]:
        raise KeyError('Locale not enabled: "{}"'.format(locale_code))
    return HTTPFound(location=request.referrer or '/',
        headers=locale_cookie_headers(locale_code))


# TODO Function that detects locale from browser


def add_template_globals(event):
    '''Makes the enabled locales dictionary readily available in
    template context.
    '''
    event['enabled_locales'] = \
        event['request'].registry.settings[SETTING_NAME]
    event['locale_code'] = get_locale_name(event['request'])  # to set xml:lang


def includeme(config):
    prepare_enabled_locales(config.get_settings())
    from pyramid.i18n import default_locale_negotiator
    config.set_locale_negotiator(default_locale_negotiator)
    config.add_route('locale', 'locale/{locale}')
    config.add_view(locale_view, route_name='locale')
    from pyramid.interfaces import IBeforeRender
    config.add_subscriber(add_template_globals, IBeforeRender)


# Colander and Deform section
# ===========================

def locale_exists_validator(settings):
    '''If you use Deform or even just Colander, you can use this to get a
    validator that you can use on your user preferences form,
    so a user can only choose a locale that is enabled in the system.

    TODO: Test this new implementation.
    '''
    from colander import Invalid
    enabled_locales = settings[SETTING_NAME]
    def validator(node, value):
        if value not in enabled_locales:
            raise Invalid(node, _('Please select a language.'))
    return validator


def language_dropdown(settings, title=_('Locale'), name='locale',
                      blank_option_at_top=True):
    '''If you use Deform, you can use this to get a SchemaNode that lets
    the user select a locale from the enabled ones.
    '''
    import colander as c
    import deform as d
    options = [(loc.code, loc.name) for loc in \
               settings[SETTING_NAME].values()]
    options = sorted(options, key=lambda t: _(t[1]))
    if blank_option_at_top:
        options.insert(0, ('', _('--Choose--')))
    return c.SchemaNode(c.Str(), title=title, name=name,
                        validator=locale_exists_validator(settings),
                        widget=d.widget.SelectWidget(values=options))
