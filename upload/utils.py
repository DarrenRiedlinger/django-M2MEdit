from django.conf import settings
from django.core.exceptions import SuspiciousOperation

from upload.forms import MultiUploaderField
from upload.storage import make_token


STORAGE_CLASS = getattr(settings, 'UPLOAD_STORAGE', 'upload.storage.SessionStorage')
mod, klass = STORAGE_CLASS.rsplit('.', 1)
mod = __import__(mod, fromlist=[klass])
STORAGE_CLASS = getattr(mod, klass)

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
    storage_class = STORAGE_CLASS

    def __init__(self, request, form, obj=None, patch_form_validation=True):
        self.storage = self.storage_class(request)
        self.request = request
        self.object = obj
        self.tokens = []
        self.form = form
        self.prep_form(patch_form_validation)

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

    def prep_form(self, patch_form_validation):
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
                # Storage will rasie TokenError, TokenExpired, or
                # SuspicousOperation
                token = self.storage._get(uid, self.request)

                # Make sure user isn't substituting a token
                # created by another form (e.g. to use another form
                # class's more relaxed file size/mime type
                # restrictions)
                if (
                    token.form_class !=
                    '.'.join((self.form.__module__,
                              self.form.__class__.__name__))
                ):
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
                # TODO: is this redundant with patch form?
                self.tokens.append(token)

            if patch_form_validation is True:
                self.patch_form_validation()
        # form is not bound. A GET request
        else:
            for field_label in self.multiuploader_fields.iterkeys():
                self.tokens.append(make_token(self.form, field_label))
            self.update_response()

    def update_response(self):
        self.storage._store(self.tokens)

    def remove_tokens(self):
        self.storage._remove(self.tokens)

    def patch_form_validation(self):
        """
        Following form validation, we either need to remove our tokens if the
        form was valid, or update the tokens (in case the storage has an
        expiration) when the form is invalid.  This can be done by modifying
        the view to include calls to update_response and remove_tokens,
        respectively.  But, if you have many views to update this gets
        unwieldy.  Creating a special Form subclass is a possibility, but you
        still need to pass the request into the form.  Alternatively, we can
        have our call to prep_form also take care of overriding the form's
        is_valid method.  That is what this method is for.
        """
        original_is_valid = self.form.is_valid

        def new_is_valid():
            if original_is_valid():
                self.remove_tokens()
                return True
            else:
                self.update_response()
                return False
        self.form.is_valid = new_is_valid
