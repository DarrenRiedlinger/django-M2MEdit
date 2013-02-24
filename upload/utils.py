from django.core.exceptions import SuspiciousOperation
from upload.storage import SessionStorage, CookieStorage, FileSetToken, make_token
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
    storage_class = SessionStorage

    def __init__(self, request, obj=None):
        self.storage = self.storage_class(request)
        self.request = request
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

    def prep_form(self, form):
        self.form = form
        """
        Prepare a form for validation
        """
        # See if this is a POST request
        if self.form.is_bound:
            for label, field in self.multiuploader_fields.iteritems():
                try:
                    uid = self.form.data[label + '_0']  # MultiWidget 0 is uid
                except KeyError:
                    raise SuspiciousOperation(
                            "User did not POST  hidden field %s of %s.%s" % (
                                label,
                                self.form.__module__,
                                self.form.__class__.__name__
                            )
                    )
                # Get token. Let storage riase exception if need be
                token = self.storage._get(uid, self.request)

                # Make sure user isn't substituting a token
                # created by another form (e.g. to use another form
                # class's more relaxed file size/mime type
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

                # TODO: we can get a bit fancier here by comparing the
                # fields 'initial' pks with our token.pks and possibly
                # taking a union of the two (to prevent contention between
                # to concurrent users editing the form)

                # Make form.data mutable
                self.form.data = self.form.data.copy()
                # replace hiden field's pks with our newly created
                # fileset pk
                self.form.data[label + '_1'] = ','.join(
                        [str(pk) for pk in token.pks])
                # Add token, so it will be updated (needed if form fails
                # validation)
                self.tokens.append(token)
        # form is not bound. A GET request
        else:
            for label, field in self.multiuploader_fields.iteritems():
                # if a dyanmic initial value dict was passed to the form
                # class (perhaps by a modelform), that will have precedence
                # over the field intial, so will need that pks list
                try:
                    pks = self.form.initial[label]
                    uid = field.uid
                # No dynamic initial value on form
                except KeyError:
                    uid, pks = field.initial
                self.tokens.append(make_token(uid, pks, self.form, label))

    def update_response(self, response):
        self.storage._store(self.tokens, response, self.request)

    def remove_tokens(self, response):
        self.storage.remove(self.tokens, response)
