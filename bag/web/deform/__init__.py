#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''This package:

* constitutes a third layer of templates on top of the package
  *deform_boostrap*, which skins Deform with Twitter's "bootstrap" library.
* will contain special widgets for Deform.

Our alterations to Deform templates are in the "templates" subdirectory.

Our preferred way of enabling the whole stack is this::

    starter.enable_deform((
        'bag:web/deform/templates',
        'deform_bootstrap:templates',
        'deform:templates',
    ))  # This way you do not config.include('deform_bootstrap')

Here are the changes we've made:

* mapping_item.pt: Allows you to pass a *css_class* to any mapping schema, and
  the class appears on the outer item.
* password.pt: Supports *maxlength* and *placeholder* and
  automatically sets *required*.
* textarea.pt: Supports *maxlength* and *placeholder* and
  automatically sets *required*.
* textinput.pt: Supports *maxlength* and *placeholder* and
  automatically sets *required*.
* checkbox.pt: Allows you to pass a *text* argument to a Boolean schema, and
  the text appears on the right of the checkbox.

This has been tested against deform_bootstrap 0.1a5.
'''


"""
from __future__ import unicode_literals  # unicode by default
from __future__ import absolute_import
import deform as d


class SlugWidget(d.widget.TextInputWidget):
    '''Lets you pass a *prefix* which will appear just before the <input>.
    TODO: This feature is probably no longer necessary
    since deform_bootstrap has *input_prepend* and *input_append*.
    '''
    # TODO: Make the slug input reflect the content of another input
    template = 'slug'
"""
