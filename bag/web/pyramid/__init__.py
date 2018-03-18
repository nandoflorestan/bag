"""Reusable code that might be useful for Pyramid apps."""

from pyramid.i18n import TranslationStringFactory
_ = TranslationStringFactory('bag')
del TranslationStringFactory
