from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.views.generic import ListView, DetailView, DeleteView, UpdateView, CreateView
from demoapp.forms import DemoForm
from demoapp.models import DemoModel
from upload.models import FileSet
from django.core.exceptions import PermissionDenied
from upload.utils import MultiuploadAuthenticator
import uuid
# Create your views here.


class MultiuploadMixin(object):
    def get_form(self, form_class):
        form = super(MultiuploadMixin, self).get_form(form_class)
        try:
            MultiuploadAuthenticator(self.request, form)
        except PermissionDenied as e:
            import ipdb; ipdb.set_trace()

        return form

    #def get(self, request, *args, **kwargs):
    #    import ipdb; ipdb.set_trace()
    #    return super(MultiuploadMixin, self).get(request, *args, **kwargs)

    #def form_valid(self, form):
    #    response = super(MultiuploadMixin, self).form_valid(form)
    #    import ipdb; ipdb.set_trace()
    #    self.authenticator.remove_tokens(response)
    #    return response

    #def form_invalid(self, form):
    #    response = super(MultiuploadMixin, self).form_invalid(form)
    #    import ipdb; ipdb.set_trace()
    #    self.authenticator.update_response(response)
    #    return response


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


def demo(request):
    if request.method == 'POST':
        pass

    else:
        form = DemoForm()
        request.set

    return render('new_demo.html')


def demo(request):
    # settings for the file upload
    #   you can define other parameters here
    #   and check validity late in the code
    options = {
        # the maximum file size (must be in bytes)
        "maxfilesize": 100 * 2 ** 20, # 100 Mb
        # the minimum file size (must be in bytes)
        "minfilesize": 1 * 2 ** 1, # 1 bit
        # the file types which are going to be allowed for upload
        #   must be a mimetype
        "acceptedformats": ( # NB.  Currently disabled file checks below
            "image/jpeg",
            "image/png",
            "application/msword",
            )
    }


    if request.method == 'POST':
        try:
            uid = request.session['file_upload_key']
        except AttributeError:
            return HttpResponse('Please enable cookies and try again.')

        form = DemoForm(request.POST)
        if form.is_valid():
            model_instance = DemoModel()
            model_instance.sometext = form.cleaned_data['sometext']
            model_instance.save()
            #model_instance.attachments.add(*FileUpload.objects.filter(uid=uid).all())
            model_instance.save()
            try:
                del request.session['file_upload_key']
            except KeyError:
                pass

            return HttpResponseRedirect(reverse('demoapp.views.demo'))

    if request.method == 'GET':
        form = DemoForm()
        uid = uuid.uuid4().hex
        request.session['file_upload_key'] = uuid.uuid4().hex

    model_instances = DemoModel.objects.all()


    return render_to_response(
            'demoapp.html',
            {'model_instances': model_instances,
                'form': form,
                'maxfilesize': options['maxfilesize'],
                'minfilesize': options['minfilesize'],
                },
            context_instance=RequestContext(request)
            )
