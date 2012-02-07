#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''This package contains special widgets for Deform.

Also, alterations have been made to the templates of stock Deform widgets.
They are in the "templates" subdirectory. This means you have to add it
to your deform template directories. For instance:

    starter.enable_deform(['bag:web/deform/templates', 'deform:templates'])

Here are the changes we've made:

* textinput.pt: Allows you to pass a `maxlength` and sets this attribute on
  the <input>.
* mapping_item.pt: Allows you to pass a `css_class` to any mapping schema, and
  the class appears on the <li>.
* checkbox.pt: Allows you to pass a `text` argument to a Boolean schema, and
  the text appears on the right of the checkbox.

SlugWidget
==========

Lets you pass a `prefix` which will appear just before the <input>.

'''

from __future__ import unicode_literals  # unicode by default
from __future__ import absolute_import
import deform as d


class SlugWidget(d.widget.TextInputWidget):
    # TODO: Make the slug input reflect the content of another input
    template = 'slug'
