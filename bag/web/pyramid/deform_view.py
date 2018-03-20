"""Abstract base classes for creating deform views in Pyramid."""

from itertools import count
from typing import Optional
from pyramid.decorator import reify
from pyramid.i18n import get_localizer
from pyramid.threadlocal import get_current_request
import colander as c
import deform as d
import peppercorn
from . import _


def translator(term):
    return get_localizer(get_current_request()).translate(term)


def button(title=_('Submit'), name=None, icon=None):
    """Conveniently generate a Deform button while setting its
    ``name`` attribute, translating the label and capitalizing it.
    The button may also have a bootstrap icon.
    """
    b = d.Button(title=translator(title).capitalize(),
                 name=name or title.lower())
    b.icon = icon
    return b


class BaseDeformView(object):
    """An abstract base class (ABC) for Pyramid views that use deform.

    The workflow is divided into several methods so you can change details
    easily in subclasses.

    Subclasses must provide at least:

    * a static *schema*. (This should subclass deform's CSRFSchema.)
    * one or more view methods that use the methods in this ABC, especially
      *_deform_workflow()* or *_colander_workflow()*.

    Example usage::

        from deform.schema import CSRFSchema
        from bag.web.pyramid.deform_view import BaseDeformView

        class InvitationView(BaseDeformView):
            formid = 'invitation_form'
            button_text = _("Send invitations to the above users")
            button_icon = 'icon-envelope icon-white'
            schema = MyInvitationSchema  # a CSRFSchema subclass

            @view_config(name='invite-users',
                         renderer='myapp:templates/invite-users.genshi')
            def invite_users(self):
                return self._deform_workflow()

            def _valid(self, form, controls):
                '''The form validates, so now we send out the invitations,
                set up a flash message and redirect to the home page.
                '''
                (...)

    If you want to do something with the POSTed data *before* validation,
    just implement this method in your subclass::

        def _preprocess_controls(self, controls):
    """

    button_text = _("Submit")
    button_icon = None  # type: Optional[str]
    formid = 'form'
    bootstrap_form_style = 'form-horizontal'
    schema_validator = None  # validator to be applied to the form as a whole
    use_ajax = False

    def __init__(self, context, request):
        """Set ``status`` to the request method.

        Later, ``status`` becomes 'valid' or 'invalid'.
        """
        self.context = context
        self.request = request
        self.status = request.method

    def _get_buttons(self):
        """Return the buttons tuple for instantiating the form.

        If this doesn't do what you want, override this method!
        """
        return [button(self.button_text, icon=self.button_icon)]

    @reify
    def schema_instance(self):
        """Give subclasses a chance to mutate the schema.

        Example::

            @reify
            def schema_instance(self):
                return self.schema().bind(now=datetime.utcnow())

        The default implementation binds the request for CSRF protection
        and, if ``self.schema_validator`` is defined, uses it for the
        form as a whole.
        """
        return self.schema(validator=self.schema_validator).bind(
            request=self.request)

    def _get_form(self, schema=None, **kw):
        """When there is more than one Deform form per page, forms must use
        the same *counter* to generate unique input ids. So we create the
        variable ``request.deform_field_counter``.
        """
        if not hasattr(self.request, 'deform_field_counter'):
            self.request.deform_field_counter = count()
        return d.Form(schema or self.schema_instance, **self._form_args(**kw))

    def _form_args(self, action='', bootstrap_form_style=None,
                   buttons=None, formid=None, ajax_options=None):
        """Override this to change the kwargs to the Form constructor."""
        adict = dict(
            action=action,
            buttons=buttons or self._get_buttons(),
            counter=self.request.deform_field_counter,
            formid=formid or self.formid,
            bootstrap_form_style=bootstrap_form_style or
            self.bootstrap_form_style,
            use_ajax=self.use_ajax)
        if ajax_options:
            adict['ajax_options'] = ajax_options
        return adict

    def _template_dict(self, form=None, controls=None, **k):
        """Override this method to fill in the dictionary that is returned
        to the template. This method is called in all 3 scenarios:
        initial GET, invalid POST and validated POST. If you need to know
        which situation you're in, check ``self.status``.

        By default, the returned dict will contain a rendered ``form``.
        """
        form = form or self._get_form()
        if isinstance(form, d.Form):
            form = form.render(controls) if controls else form.render()
        else:  # form must be a ValidationFailure exception
            form = form.render()
        return dict(form=form, **k)

    def _preprocess_controls(self, controls):
        """If you'd like to do something with the POSTed data *before*
        validation, just override this method in your subclass.
        """
        return controls

    def _deform_workflow(self, controls=None, form_args=None):
        """Call this from your view. This performs the whole deform validation
        step (using the other methods in this abstract base class)
        and returns the appropriate dictionary for your template.
        """
        if not form_args:
            form_args = {}
        if self.request.method == 'POST':
            return self._post(self._get_form(**form_args), controls=controls)
        else:
            return self._get(self._get_form(**form_args))

    def _load_controls(self):
        """Override this method to load existing data from your database.
        Return the data as a dict, or None if the object being edited is new.
        This is only called in GET requests.
        """
        return None

    def _get(self, form):
        """You may override this method in subclasses to do something special
        when the request method is GET.
        """
        return self._template_dict(form=form, controls=self._load_controls())

    def _post(self, form, controls=None):
        """You may override this method in subclasses to do something special.

        ...when the request method is POST.
        """
        controls = peppercorn.parse(controls or self.request.POST.items())
        controls = self._preprocess_controls(controls)
        try:
            appstruct = form.validate_pstruct(controls)
        except d.ValidationFailure as e:
            self.status = 'invalid'
            return self._invalid(e, controls)
        else:
            self.status = 'valid'
            appstruct.pop('csrf_token', None)  # Discard the CSRF token
            return self._valid(form=form, controls=appstruct)

    def _invalid(self, exception, controls):
        """Override this to change what happens upon ValidationFailure.

        By default we simply redisplay the form.
        """
        return self._template_dict(form=exception)

    def _valid(self, form, controls):
        """This is called after form validation. You may override this method
        to change the response at the end of the view workflow.
        """
        raise NotImplementedError(
            "You need to    def _valid(self, form, controls):")

    def _colander_workflow(self, controls=None):
        """Especially in AJAX views, you may skip Deform and use just colander
        for validation, returning a dictionary of errors to be displayed
        next to the form fields.
        TODO: Test
        """
        controls = controls or self.request.POST.items()
        try:
            appstruct = self._get_schema().deserialize(controls)
        except c.Invalid as e:
            return dict(errors=e.asdict2() if hasattr(e, 'asdict2')
                        else e.asdict())
        else:
            # appstruct.pop('csrf_token', None)  # Discard the CSRF token
            return appstruct
