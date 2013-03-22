from demoapp.models import DemoModel
from django.core.urlresolvers import reverse
from django.views.generic import ListView, DetailView, DeleteView, UpdateView, CreateView
from upload.utils import MultiuploadAuthenticator


# Create your views here.


class MultiuploadMixin(object):
    def get_form(self, form_class):
        form = super(MultiuploadMixin, self).get_form(form_class)
        MultiuploadAuthenticator(self.request, form)
        return form


class CrudMixin(MultiuploadMixin):
    model = DemoModel

    def get_sucess_url(self):
        return reverse('crud_list')

    def get_queryset(self):
        return self.model.objects.all()


class CrudListView(CrudMixin, ListView):
    pass


class CrudDetailView(CrudMixin, DetailView):
    pass


class CrudCreateView(CrudMixin, CreateView):
    pass


class CrudDeleteView(CrudMixin, DeleteView):
    pass


class CrudUpdateView(CrudMixin, UpdateView):
    pass
