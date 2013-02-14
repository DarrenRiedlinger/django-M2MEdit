from django.core.exceptions import SuspiciousOperation
from upload.storage import CookieStorage, FileSetToken, make_token
from upload.fields import MultiUploaderField

# NB: If, for some reason, your app uses the same form class to edit
# multiple models, for newly created model instances
# these checks aren't guaranteed to ensure that user hasn't switched the
# hidden FileSet field uuids of two newly created model-instances.  For
# example, Model A's form produces uuid A and Model B's form produces
# uuid B.  The user uploads file A to the upload link at uuid A and file
# B to uuid link B.  But, s/he then inputs uuid A into the hidden field
# of model B's form and uuid B into A's form.  I can't forsee this being
# an issue as the user could have just as easily uploaded file B to uuid
# link A (since there the same form class, the form validation is
# identical), but its worth keeping in mind if you are using this in
# unusually way.
# Do note that the modelformfactory creates a seprate
# form class for each model, so this shouldn't be an issue with the,
# e.g., generic class views.


class MultiuploadAuthenticator(object):
    storage = CookieStorage()

    def __init__(self, request, form, obj=None):
        self.request = request
        self.form = form
        self.object = obj
        self.tokens = []

    @property
    def multiuploader_fields(self):
        """
        Store a list of all multiuploader fields on the form
        """
        if not hasattr(self, '_multiuploader_fields'):
            self._multiuploader_fields = {label: field for (label, field) in
                                          self.form.fields.items() if
                                          issubclass(
                                              field.__class__,
                                              MultiUploaderField)}
        return self._multiuploader_fields

    def prep_form(self):
        """
        Prepare a form for validation
        """
        # See if this is a POST request
        if self.form.is_bound:
            for label, field in self.multiuploader_fields.iteritems():
                try:
                    hidden_field_val = self.form.data[label]
                except KeyError:
                    raise SuspiciousOperation(
                            "User deleted hidden field %s of %s.%s" % (
                                label,
                                self.form.__module__,
                                self.form.__class__.__name__
                            )
                    )
                # Get token. Let storage riase exception if need be
                token = self.storage.load(hidden_field_val, self.request)

                initial = getattr(self.form.initial, label, None)

                # form.initial['label'] will be non-None if there was an
                # existing parent model instances. If so, we just need
                # to make sure our submitted hidden_field_val matches.
                if initial:
                    if initial == hidden_field_val:
                        # In case subsequent form validation fails, we need to
                        # make self.update_response know to update this tokens
                        # timestamp
                        self.tokens.append(token)
                        continue
                    else:
                        raise SuspiciousOperation(
                                "User modified hidden field %s of %s.%s" % (
                                    label,
                                    self.form.__module__,
                                    self.form.__class__.__name__)
                        )
                # Otherwise, no initial data to rely on so we need to perform
                # more advanced checks using the token
                else:
                    # Make sure user isn't substituting a fileset/token
                    # created by another form (e.g. to use the other form
                    # classes more relxed file size/mime type
                    # restrictions)
                    if (token.form_class_name !=
                            self.form.__class__.__name__ or
                            token.form_module !=
                            self.form.__class__.__module__ or
                            token.field_label != label):
                        raise SuspiciousOperation(
                                "User modified hidden field %s of %s.%s" % (
                                    label,
                                    self.form.__module__,
                                    self.form.__class__.__name__)
                        )
                    if token.fileset_pk:
                        # replace hiden field's uuid with our newly created
                        # fileset pk
                        self.form.data[label] = token.fileset_pk
                    # NB: if token.fielset_pk is None, the model
                    # isntance still needs to be created and our user
                    # never uploaded a valid file.  We can let the
                    # formfield validators decide if they want to create
                    # a empty FileSet or raise a value required error
                    self.tokens.append(token)
        else:  # form is not bound; its a GET request
            for label, field in self.multiuploader_fields.iteritems():
                # form.initial will be set if this is an existing instance
                # Otherwise, have field generate a unique initial val
                try:
                    pk = hidden_field_value = getattr(self.form.initial,
                                                      label)
                except AttributeError:
                    hidden_field_value = field.initial
                    pk = None
                self.tokens.append(make_token(self.form, label,
                                   hidden_field_value, pk))

    def update_response(self, response, request):
        self.storage.add(self.tokens, response, request)

    def remove_tokens(self, response, request=None):
        self.storage.remove(self.tokens, response)
