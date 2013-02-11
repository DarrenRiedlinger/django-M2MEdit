
class MultiuploadAuthenticator(object):
    prefix = 'fileset'

    def __init__(self, request, form, obj=None):
        self.request = request
        self.form = form
        self.object = obj
        self.tokens = None

    @property
    def multiuploader_fields(self):
        if not hasattr(self, '_multiuploader_fields'):
            self._multiuploader_fields = {label: field for (label, field) in 
                    self.form.fields.items() if isinstance(field,
                        MultiUploaderField())}
        return self._multiuploader_fields
        
    def prep_form(self):
        """
        Prepare a form for validation
        """
        # form.data wil only be present on POST request
        if self.form.data:
            for label, field in self.multiuploader_fields:
                data = getattr(self.form.data, label, '')

                # Make sure hidden field wasn't modified
                # If instance was allready created, checking 
                if self.object is not None:
                    # Check if hidden field was tampered with
                    if data != self.object.pk:
                        raise SuspiciousOperation(("User modified hidden "
                            "field %s of %s" % (label, self.object)))
                    # TODO: making sure the fileset actually contains
                    # files will be taken care of by the formfield
                    # iteself. Furthermore, since our checks prevent the
                    # form validation from being passed a bad value, a
                    # non-existant fileset pk will be treated as a
                    # missing value error rather than an invalid choice
                else:
                    try:
                        token = self.storage.load(data)
                    except AttributeError:
                        # This assumes our view allready set test cookie
                        # TODO: This might just be an expired cookie, in which
                        # case we don't want permission denied.
                        raise PermissionDenied
                    # Make sure user isn't substituting a fileset created by
                    # another form class (e.g. to use the other form classes
                    # more relxed file size/mime type restrictions
                    if (token.module != self.form.__module__ or
                            token.form_class != self.form.__class__.__name__):
                        raise SuspiciousOperation(
                                "User modified hidden field %s of %s.%s" % (
                                    label,
                                    self.form.__module__,
                                    self.form.__class__.__name__)
                                )
                    if token.pk:
                        self.form.data[label] = token.pk
                    if not field.required:
                        # ModelField will have a callable which creates an
                        # empy fileset
                        pass
        else:  # A GET request
            for label, field in self.multiuploader_fields:
                # form.initial be set if this is an existing instance
                # Otherwise, have field generate a unique initial val
                try:
                    value = getattr(self.form.initial, label, None)
                except AttributeError:
                    value = field.initial
                token = MultiuploaderToken(value=value, field=field,
                                           label=label)
                self.tokens.append(token)

    def update_response(self, response):
        for token in self.tokens:
            self.storate.add(token)
