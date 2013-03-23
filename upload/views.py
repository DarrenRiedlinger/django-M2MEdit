from django.conf import settings
from django.http import HttpResponseRedirect
from django.views.generic import CreateView
from django.views.generic.edit import FormMixin

from upload.storage import TokenError
from upload.forms.forms import ListForm

COOKIE_LIFETIME = getattr(settings, 'UPLOAD_COOKIE_LIFETIME', 300)


STORAGE_CLASS = getattr(
    settings,
    'UPLOAD_STORAGE',
    'upload.storage.SessionStorage'
)
module, klass = STORAGE_CLASS.rsplit('.', 1)
module = __import__(module, fromlist=[klass])
STORAGE_CLASS = getattr(module, klass)


class M2MEdit(CreateView):
    #template_name_suffix = '_m2m_form.html'
    template_name = 'upload_form.html'
    missing_cookie_template = 'missing_cookie.html'
    storage_class = STORAGE_CLASS

    def get_sucess_url(self):
        # There is no success url, we just redirect back to GET
        return HttpResponseRedirect('')

    def get_form_kwargs(self, **kwargs):
        """
        Override get_form_kwargs to itself take kwargs.
        """
        # our ListForm can't handle the 'instance' kwarg, so we don't call
        # ModelFormMixin as super
        keywords = FormMixin.get_form_kwargs(self)
        keywords.update(kwargs)
        return keywords

    def get_forms(self):
        module = __import__(self.token.model_module,
                            fromlist=[self.token.model_class_name])
        self.model = getattr(module, self.token.model_class_name)
        CreationForm = self.get_form_class()
        creation_form = CreationForm(**self.get_form_kwargs(prefix='creation',
                                                            empty_permitted=True))
        if self.token.pks:
            list_form = self.get_list_form()
        else:
            list_form = None
        return creation_form, list_form

    def get_list_form(self):
        queryset = self.model._default_manager.filter(pk__in=self.token.pks)
        return ListForm(**self.get_form_kwargs(prefix='list',
                                               queryset=queryset))

    def get(self, request, *args, **kwargs):
        self.object = None
        self.storage = self.storage_class(request)
        self.uid = kwargs['uid']
        try:
            self.token = self.storage._get(self.uid)
        except TokenError as e:
            return self.render_to_response(self.get_context_data(
                                           exception=e))
        creation_form, list_form = self.get_forms()
        return self.render_to_response(self.get_context_data(
            creation_form=creation_form, list_form=list_form))

    def post(self, request, *args, **kwargs):
        # TODO: will need to further modify TemporaryUploadedFile class to
        # customize where this app's temp files are stored.

        self.object = None
        self.storage = self.storage_class(request)
        self.uid = kwargs['uid']
        try:
            self.token = self.storage._get(self.uid)
        # Most likely because they hit the back button after submitting parent
        # form.
        except TokenError as e:
            return self.render_to_response(self.get_context_data(
                                           exception=e))
        creation_form, list_form = self.get_forms()
        if (creation_form.is_valid() and
           (list_form is None or list_form.is_valid())):
            return self.form_valid(creation_form, list_form)
        else:
            return self.form_invalid(creation_form, list_form)

    def form_valid(self, creation_form, list_form):
        if list_form and list_form.has_changed():
            selected = set([obj.pk for obj in
                        list_form.cleaned_data['existing_objects']])
            self.token.pks = list(set(self.token.pks) - selected)
            # immediately delete any selected instances selected that were
            # uploaded during this same M2M edit
            delete_pks = selected - set(self.token.original_pks)
            self.model._default_manager.filter(pk__in=delete_pks).delete()
        # If anything was submitted to the creation form
        if creation_form.has_changed():
            obj = creation_form.save()
            self.token.pks.append(obj.pk)
        response = HttpResponseRedirect('')
        self.storage._store([self.token], response=response)
        return response

    def form_invalid(self, creation_form, list_form):
        return self.render_to_response(self.get_context_data(
                creation_form=creation_form, list_form=list_form))
