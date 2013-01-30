from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.shortcuts import render_to_response

from demoapp.forms import DemoForm
from demoapp.models import DemoModel
from upload.models import FileUpload

import uuid
# Create your views here.

def demo(request):
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

            model_insance.attachments.add(FileUpload.objects.filter(uid=uid).all())
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
                'form': form},
            context_instance=RequestContext(request)
            )
