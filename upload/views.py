# imports

# import the django settings
from django.conf import settings
# for generating json
from django.utils import simplejson
from django.utils.encoding import smart_unicode
# for loading template
from django.template import Context, loader
# for csrf
from django.core.context_processors import csrf
# for HTTP response
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
# for os manipulations
import os
from django.views.generic import CreateView
from django.views.generic.edit import FormMixin
from django.utils.translation import ugettext as _
from django.http import Http404
from django.core.signing import BadSignature, SignatureExpired
from django.core.exceptions import PermissionDenied, SuspiciousOperation, ObjectDoesNotExist

from upload.forms import FileUploadForm, FileSetForm
from upload.models import FileSet, File
from django.shortcuts import render_to_response, render
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.conf import settings
from django.core.files.uploadhandler import TemporaryFileUploadHandler
from sorl.thumbnail import get_thumbnail

from functools import partial

COOKIE_LIFETIME = getattr(settings, 'UPLOAD_COOKIE_LIFETIME', 300)

from upload.storage import CookieStorage, SessionStorage
from upload.forms import CheckboxSelectFiles
from django import forms


class CustomModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    """
    A ModelMultipleChoiceField that optionally uses a model's __html__() method
    to render the choice field's label.
    """
    def label_from_instance(self, obj):
        if hasattr(obj, '__html__'):
            return obj.__html__()
        else:
            return super(CustomModelMultipleChoiceField,
                         self).label_from_instance(obj)


class ListForm(forms.Form):
    def __init__(self, queryset, *args, **kwargs):
        super(ListForm, self).__init__(*args, **kwargs)
        self.fields['existing_objects'] = CustomModelMultipleChoiceField(
                                              queryset=queryset,
                                              widget=forms.CheckboxSelectMultiple,
                                              required=False)


class M2MEdit(CreateView):
    #template_name_suffix = '_m2m_form.html'
    template_name = 'upload_form.html'
    storage_class = SessionStorage
    #def get_form_class(self):
    #    if self.object:
    #        return partial(FileSetForm, self.object.pk)
    #    return partial(FileSetForm, None)

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
        self.storage = self.storage_class(request)
        self.uid = kwargs['uid']
        self.token = self.storage._get(self.uid)
        self.object = None
        creation_form, list_form = self.get_forms()
        return self.render_to_response(self.get_context_data(
            creation_form=creation_form, list_form=list_form))

    def post(self, request, *args, **kwargs):
        # TODO: will need to further modify TemporaryUploadedFile class to
        # customize where this app's temp files are stored.

        # Prevent file from being uploaded in-memory.  This is so we can
        # serve the file before it is saved.
        request.upload_handlers = [TemporaryFileUploadHandler()]

        self.storage = self.storage_class(request)
        self.uid = kwargs['uid']
        self.token = self.storage._get(self.uid)
        self.object = None
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


def edit_file_set(request, file_set_pk):
    try:
        file_set = FileSet.objects.get(pk=file_set_pk)
    except AttributeError:
        raise Http404(_("No matching fileset found"))
    # Make sure user is coming from a view that set the appropriate cookie
    # try:
    #     cookie = request.get_signed_cookie('file_set%s' % file_set_pk,
    #             max_age=COOKIE_LIFETIME, httponly=True)
    # except KeyError, SignatureExpired:
    #     raise PermissionDenied(_(("You either tried to acess the page ",
    #         "directly, your browser does not have cookies enabled, or your ",
    #         "session has expired. Please press 'back' in your broswer, ensure",
    #         "that you have cookies enabled and try again")))
    # except BadSignature:
    #     raise SuspiciousOperation(_("Cookie Signature Invalid"))

    FileSetInstanceForm = partial(FileSetForm, file_set_pk)

    if request.method == 'POST':
        form = FileSetInstanceForm(request.POST, request.FILES)
        if form.is_valid():
            # TODO: Will need to store max size and mimetype
            # in session, and then verify here
            error = False
            [file_set.files.remove(f.pk) for f in form.cleaned_data['current_files']]
            if request.FILES:
                newfile = File(document=request.FILES['file_upload'])
                # After save, document.name gets appended to path and possibly
                # gets appended with a version number.  We're saving the original
                # filename here for easy acess without having to strip the path and
                # version number.
                # TODO: Do I need to escape the original filename?
                newfile.filename = newfile.document.name
                newfile.save()
                try:
                    image = get_thumbnail(newfile.document, "80x80", quality=50)
                    newfile.thumb_url = image.url
                    newfile.save()
                except (IOError, OverflowError):
                    # Image not recognized by sorl
                    pass

                file_set.files.add(newfile)
                file_set.save()


            # since jquery file_upload iframe transport won't be ajax,
            # also test for our explicit querystring
            if request.is_ajax() or request.GET.get('use_ajax', False):
                response_data = {
                        "name" : newfile.filename,
                        "size" : newfile.document.size,
                        "type" : request.FILES['file_upload'].content_type
                        }
                # Append Errors

                response_data = simplejson.dumps([response_data])

                # QUIRK HERE
                # in jQuey uploader, when it falls back to uploading using iFrames
                # the response content type has to be text/html
                # if json will be send, error will occur
                # if iframe is sending the request, it's headers are a little different compared
                # to the jQuery ajax request
                # they have different set of HTTP_ACCEPT values
                # so if the text/html is present, file was uploaded using jFrame because
                # that value is not in the set when uploaded by XHR
                if 'application/json'  in request.META["HTTP_ACCEPT"]:
                    response_type = "application/json"
                else:
                    response_type = 'text/html'

                return HttpResponse(response_data,
                        mimetype=response_type)

            else: # Normal HTML request
                # Redirect back to this page after post
                return HttpResponseRedirect(reverse(
                    'upload.views.uid_upload',
                    kwargs={'uid': file_set.pk} ))
    else:
        form = FileSetInstanceForm()

    return render(request, 'edit_file_set.html',
        { 'form': form, 'file_set': file_set }
        )




def new_upload(request):
    try:
        uid= request.session['file_upload_key']
    except KeyError:
        return HttpResponse(("Error.  You've either tried to access this page",
                " directly, or you do not have cookies enabled. If it is the ",
                "latter, please enable cookies and try again."))

    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # TODO: Will need to store max size and mimetyple
            # in session, and then verify here
            error = False
            newfile = FileUpload(document = request.FILES['file_upload'])
            # After save, document.name gets appended to path and possibly
            # gets appended with a version number.  We're saving the original
            # filename here for easy acess without having to strip the path and
            # version number.
            # TODO: Do I need to escape the original filename?
            newfile.filename = newfile.document.name
            newfile.uid = request.session['file_upload_key']
            newfile.save()

            # since iframe won't be ajax, also test for our querystring
            if request.is_ajax() or \
                    request.GET.get('use_ajax', 'false') == 'true':
                response_data = {
                    "name" : newfile.filename,
                    "size" : newfile.document.size,
                    "type" : request.FILES['file_upload'].content_type
                }
                # Append Errors

                response_data = simplejson.dumps([response_data])

                response_type = 'text/html'
                # QUIRK HERE
                # in jQuey uploader, when it falls back to uploading using iFrames
                # the response content type has to be text/html
                # if json will be send, error will occur
                # if iframe is sending the request, it's headers are a little different compared
                # to the jQuery ajax request
                # they have different set of HTTP_ACCEPT values
                # so if the text/html is present, file was uploaded using jFrame because
                # that value is not in the set when uploaded by XHR
                if 'application/json'  in request.META["HTTP_ACCEPT"]:
                    response_type = "application/json"

                return HttpResponse(response_data,
                        mimetype=response_type)

            else: # Normal HTML request
               # Redirect to the document list after POST
               return HttpResponseRedirect(reverse('upload.views.new_upload'))

    if request.method == 'GET':
        form = FileUploadForm()

    files = FileUpload.objects.filter(uid=request.session['file_upload_key'])

    return render_to_response(
            'new_upload.html',
            {'files': files, 'form': form},
            context_instance=RequestContext(request)
            )

def upload(request):
    """

    ## View for file uploads ##

    It does the following actions:
        - displays a template if no action have been specified
        - upload a file into unique temporary directory
                unique directory for an upload session
                    meaning when user opens up an upload page, all upload actions
                    while being on that page will be uploaded to unique directory.
                    as soon as user will reload, files will be uploaded to a different
                    unique directory
        - delete an uploaded file

    ## How Single View Multi-functions ##

    If the user just goes to a the upload url (e.g. '/upload/'), the request.method will be "GET"
        Or you can think of it as request.method will NOT be "POST"
    Therefore the view will always return the upload template

    If on the other side the method is POST, that means some sort of upload action
    has to be done. That could be either uploading a file or deleting a file

    For deleting files, there is the same url (e.g. '/upload/'), except it has an
    extra query parameter. Meaning the url will have '?' in it.
    In this implementation the query will simply be '?f=filename_of_the_file_to_be_removed'

    If the request has no query parameters, file is being uploaded.

    """

    # used to generate random unique id
    import uuid

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


    # POST request
    #   meaning user has triggered an upload action
    if request.method == 'POST':
        # figure out the path where files will be uploaded to
        # PROJECT_ROOT is from the settings file
        temp_path = os.path.join(settings.PROJECT_ROOT, "tmp")

        # if 'f' query parameter is not specified
        # file is being uploaded
        if not ("f" in request.GET.keys()): # upload file

            # make sure some files have been uploaded
            if not request.FILES:
                return HttpResponseBadRequest('Must upload a file')

            # make sure unique id is specified - VERY IMPORTANT
            # this is necessary because of the following:
            #       we want users to upload to a unique directory
            #       however the uploader will make independent requests to the server
            #       to upload each file, so there has to be a method for all these files
            #       to be recognized as a single batch of files
            #       a unique id for each session will do the job
            if not request.POST[u"uid"]:
                return HttpResponseBadRequest("UID not specified.")
                # if here, uid has been specified, so record it
            uid = request.POST[u"uid"]

            # update the temporary path by creating a sub-folder within
            # the upload folder with the uid name
            temp_path = os.path.join(temp_path, uid)

            # get the uploaded file
            file = request.FILES[u'files[]']

            # initialize the error
            # If error occurs, this will have the string error message so
            # uploader can display the appropriate message
            error = False

            # check against options for errors

            # file size
            if file.size > options["maxfilesize"]:
                error = "maxFileSize"
            if file.size < options["minfilesize"]:
                error = "minFileSize"
                # allowed file type
#            if file.content_type not in options["acceptedformats"]:
#                error = "acceptFileTypes"


            # the response data which will be returned to the uploader as json
            response_data = {
                "name": file.name,
                "size": file.size,
                "type": file.content_type
            }

            # if there was an error, add error message to response_data and return
            if error:
                # append error message
                response_data["error"] = error
                # generate json
                response_data = simplejson.dumps([response_data])
                # return response to uploader with error
                # so it can display error message
                return HttpResponse(response_data, mimetype='application/json')


            # make temporary dir if not exists already
            if not os.path.exists(temp_path):
                os.makedirs(temp_path)

            # get the absolute path of where the uploaded file will be saved
            # all add some random data to the filename in order to avoid conflicts
            # when user tries to upload two files with same filename
            filename = os.path.join(temp_path, str(uuid.uuid4()) + file.name)
            # open the file handler with write binary mode
            destination = open(filename, "wb+")
            # save file data into the disk
            # use the chunk method in case the file is too big
            # in order not to clutter the system memory
            for chunk in file.chunks():
                destination.write(chunk)
                # close the file
            destination.close()

            # here you can add the file to a database,
            #                           move it around,
            #                           do anything,
            #                           or do nothing and enjoy the demo
            # just make sure if you do move the file around,
            # then make sure to update the delete_url which will be send to the server
            # or not include that information at all in the response...

            # allows to generate properly formatted and escaped url queries
            import urllib

            # url for deleting the file in case user decides to delete it
            response_data["delete_url"] = request.path + "?" + urllib.urlencode(
                    {"f": uid + "/" + os.path.split(filename)[1]})
            # specify the delete type - must be POST for csrf
            response_data["delete_type"] = "POST"

            # generate the json data
            response_data = simplejson.dumps([response_data])
            # response type
            response_type = "application/json"

            # QUIRK HERE
            # in jQuey uploader, when it falls back to uploading using iFrames
            # the response content type has to be text/html
            # if json will be send, error will occur
            # if iframe is sending the request, it's headers are a little different compared
            # to the jQuery ajax request
            # they have different set of HTTP_ACCEPT values
            # so if the text/html is present, file was uploaded using jFrame because
            # that value is not in the set when uploaded by XHR
            if "text/html" in request.META["HTTP_ACCEPT"]:
                response_type = "text/html"

            # return the data to the uploading plugin
            return HttpResponse(response_data, mimetype=response_type)

        else: # file has to be deleted

            # get the file path by getting it from the query (e.g. '?f=filename.here')
            filepath = os.path.join(temp_path, request.GET["f"])

            # make sure file exists
            # if not return error
            if not os.path.isfile(filepath):
                return HttpResponseBadRequest("File does not exist")

            # delete the file
            # this step might not be a secure method so extra
            # security precautions might have to be taken
            os.remove(filepath)

            # generate true json result
            # in this case is it a json True value
            # if true is not returned, the file will not be removed from the upload queue
            response_data = simplejson.dumps(True)

            # return the result data
            # here it always has to be json
            return HttpResponse(response_data, mimetype="application/json")

    else: #GET
        # load the template
        t = loader.get_template("upload.html")
        c = Context({
            # the unique id which will be used to get the folder path
            "uid": uuid.uuid4(),
            # these two are necessary to generate the jQuery templates
            # they have to be included here since they conflict with django template system
            "open_tv": u'{%',
            "close_tv": u'%}',
            # some of the parameters to be checked by javascript
            "maxfilesize": options["maxfilesize"],
            "minfilesize": options["minfilesize"],
            })
        # add csrf token value to the dictionary
        c.update(csrf(request))
        # return
        return HttpResponse(t.render(c))

