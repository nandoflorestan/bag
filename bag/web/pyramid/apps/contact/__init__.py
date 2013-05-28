# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import colander as c
import deform as d
from ... import _
from ...starter import register_view_class
from ..views import BaseView


def create_contact_view(config, BaseView=BaseView, route_name='contact',
        action='', renderer=None, master_template='aaa.genshi',
        len_name=dict(min=2, max=200),
        len_subject=dict(max=256),
        len_message=dict(max=80 * 500),
        subject_prefix='[Contact form]', impersonate=False):
    '''Returns a generic view for a contact form page which sends email
    using marrow.mailer.

    You should probably use:

        pyramid_starter.enable_marrow_mailer()
        pyramid_starter.enable_genshi()

    The returned view can be reused in multiple web applications. Example:

        from bag.web.pyramid.apps.contact import create_contact_view
        ContactView = create_contact_view()

    *action* defines where the form POSTs to.
    '''
    if not renderer:  # No renderer was passed, so use our default template
        import os
        here = os.path.realpath(os.path.dirname(__file__))
        renderer = here + '/contact.genshi'

    @register_view_class
    class ContactView(BaseView):
        @staticmethod
        def declare_routes(config, prefix=''):
            config.add_route(route_name, prefix + 'contact')
            config.add_view(route_name=route_name, view=ContactView,
                renderer=renderer, request_method='GET', attr='get')
            config.add_view(route_name=route_name, view=ContactView,
                renderer=renderer, request_method='POST', attr='post')

        def __init__(self, request):
            self.request = request

        def _get_form(self):
            return d.Form(self.ContactSchema(), buttons=(_('Send email'),),
                action=action, formid='contact-form')

        def _template_context(self, contact_form=None):
            return dict(pagetitle=_("Contact"), contact_form=contact_form,
                        master_template=master_template)

        def get(self):
            '''Displays the contact form.'''
            return self._template_context(self._get_form().render())

        def post(self):
            '''Sends out an email if POSTed data validates;
            else redisplays the form with the error messages.
            '''
            controls = self.request.POST.items()
            try:
                appstruct = self._get_form().validate(controls)
            except d.ValidationFailure as e:
                # If form does not validate, return the form
                return self._template_context(e.render())
            # Form validation passes, so send out the e-mail
            self._send(**appstruct)
            return self._on_success()

        def _assemble_msg(self, **kw):
            return msg_template.format(**kw)

        def _send(self, **k):
            if impersonate:
                msg = self.request.registry.mailer.new(
                    author=(k['name'], k['email']),
                    plain=self._assemble_msg(**k),
                    subject='{} {}'.format(subject_prefix, k['subject']))
            else:  # Author will come from configuration
                msg = self.request.registry.mailer.new(
                    plain=self._assemble_msg(**k),
                    subject='{} {}'.format(subject_prefix, k['subject']))
            msg.send()

        def _on_success(self):
            '''By default, after the email is sent, the contact form
            appears again. Override this method to change this behaviour.
            '''
            return dict(email_sent=True, master_template=master_template)

        class ContactSchema(c.MappingSchema):
            name = c.SchemaNode(c.Str(), title=_('Name'),
                widget=d.widget.TextInputWidget(size=60, maxlength=160))
            email = c.SchemaNode(c.Str(), title=_('Email'),
                validator=c.Email(),
                widget=d.widget.TextInputWidget(size=50, maxlength=160,
                    type='email'))
            subject = c.SchemaNode(c.Str(), title=_('Subject'),
                widget=d.widget.TextInputWidget(size=60, maxlength=160))
            message = c.SchemaNode(c.Str(), title=_('Message'),
                    widget=d.widget.TextAreaWidget(cols=60, rows=12))
            if len_name:
                name.widget.maxlength = len_name.get('max')
                name.validator = c.Length(**len_name)
            if len_subject:
                subject.validator = c.Length(**len_subject)
            if len_message:
                message.validator = c.Length(**len_message)
    return ContactView


msg_template = """Message sent via contact form by:
{name} <{email}>
Subject: {subject}

{message}"""
