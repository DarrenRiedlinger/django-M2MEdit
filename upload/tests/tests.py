"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from upload.fields import MultiUploaderField
from upload.models import File
from upload.utils import MultiuploadAuthenticator
from upload.storage import TokenError, FileSetToken
from upload.views import M2MEdit, ListForm
from .forms import SimpleRequiredForm, DifferentRequiredForm
from .model_factory import file_factory
from django.test.utils import override_settings
from django.test.client import RequestFactory
from django.core.exceptions import SuspiciousOperation
from django import forms
import tempfile
import copy
import shutil
from StringIO import StringIO


BASE_TOKEN = FileSetToken(
        uid='1234',
        pks=[],
        original_pks=[],
        field_label='attachments',
        form_class_name='SimpleRequiredForm',
        form_module='upload.tests.forms',
        model_class_name='File',
        model_module='upload.models',
        )


class SessionDict(dict):
    pass


class MockRequest(object):
    def __init__(self):
        self.session = SessionDict()
        self.session.session_key = 'abcde'


class MultiUploaderFieldTest(TestCase):
    def setUp(self):
        pass

    def test_field_no_initial(self):
        """
        Ensure the field generates ['uid', [pklist] when no
        initial data is provided
        """
        field = MultiUploaderField()
        self.assertEqual(field.initial, [field.uid, []])

    def test_field_w_initial(self):
        """
        Ensure field generates uid when initial is provided
        """
        field = MultiUploaderField(initial=[1,2,3])
        self.assertEqual(field.initial, [field.uid, [1,2,3]])

    def test_field_compress(self):
        """
        Ensures field can convert from a uuid, pklist back to jsut the pklist
        """
        field = MultiUploaderField()
        self.assertEqual(field.compress(['a_random_uid', [1,2,3]]), [1,2,3])


class MultiUploadAuthenticatorTest(TestCase):
    TEMP_MEDIA_ROOT = tempfile.mkdtemp()

    def setUp(self):
        self.request = MockRequest()

    def tearDown(self):
        shutil.rmtree(self.TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_form_GET_no_initial(self):
        form = SimpleRequiredForm()
        MultiuploadAuthenticator(self.request, form)
        self.assertEqual(len(self.request.session), 1)
        token = self.request.session.values()[0]
        self.assertEqual(token.pks, [])
        self.assertEqual(token.field_label, 'attachments')
        self.assertEqual(token.uid, form.fields['attachments'].uid)

    def test_form_GET_w_initial(self):
        form = SimpleRequiredForm(initial={'attachments': [1,2,3]})
        MultiuploadAuthenticator(self.request, form)
        self.assertEqual(len(self.request.session), 1)
        token = self.request.session.values()[0]
        self.assertEqual(token.pks, [1,2,3])
        self.assertEqual(token.field_label, 'attachments')
        self.assertEqual(token.uid, form.fields['attachments'].uid)

    def test_form_POST_invalid(self):
        token = copy.deepcopy(BASE_TOKEN)
        token.pks = [2,3,4]
        self.request.session['_uploads' + token.uid] = token
        form = SimpleRequiredForm({'attachments_0': token.uid,
                                   'attachments_1': '1,2'})
        MultiuploadAuthenticator(self.request, form)
        self.assertEqual(form.data['attachments_1'], '2,3,4')
        # Form will fail validation since these pks don't exist,
        # but we can verify that the form was patched to update storage
        self.request.session = {}
        self.assertEqual(len(self.request.session), 0)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(self.request.session), 1)

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_form_POST_valid(self):
        files = []
        for i in range(3):
            files.append(file_factory())
        file_pks = [f.pk for f in files]
        str_pks = ','.join([str(pk) for pk in file_pks])

        token = copy.deepcopy(BASE_TOKEN)
        token.pks = file_pks
        self.request.session['_uploads' + token.uid] = token

        form = SimpleRequiredForm({'attachments_0': token.uid,
            'attachments_1': '1,2'})
        MultiuploadAuthenticator(self.request, form)
        self.assertEqual(form.data['attachments_1'], str_pks)
        self.assertEqual(len(self.request.session), 1)
        self.assertTrue(form.is_valid())
        # Verify token was deleted after form verfication
        self.assertEqual(len(self.request.session), 0)
        self.assertEqual(set(form.cleaned_data['attachments']),
                         set(files))
    
    def test_form_POST_no_token(self):
        form = SimpleRequiredForm({'attachments_0': 'a_uid',
                                   'attachments_1': '1,2'})
        self.assertRaises(TokenError, MultiuploadAuthenticator, self.request,
                          form)
    
    def test_form_POST_switched_form(self):
        """
        If a user is editing two forms at once and swaps their tokens
        """
        token = copy.deepcopy(BASE_TOKEN)
        self.request.session['_uploads' + token.uid] = token
        form = DifferentRequiredForm({'attachments_0': token.uid,
                                   'attachments_1': '1,2,3'})
        self.assertRaises(SuspiciousOperation,
                MultiuploadAuthenticator, self.request, form)
    
    def test_form_POST_no_uid(self):
        # Simulate GET so tokens are added to session
        form = SimpleRequiredForm(initial={'attachments': [1,2,3]})
        MultiuploadAuthenticator(self.request, form)

        form = SimpleRequiredForm({'attachments_1': '1,2,3'})
        self.assertRaises(SuspiciousOperation,
                MultiuploadAuthenticator, self.request, form)

class UploadViewTest(TestCase):
    TEMP_MEDIA_ROOT = tempfile.mkdtemp()

    def setUp(self):
        self.factory = RequestFactory()

    def tearDown(self):
        shutil.rmtree(self.TEMP_MEDIA_ROOT, ignore_errors=True)
   
    def test_empty_token_pks_GET(self):
        token = copy.deepcopy(BASE_TOKEN)
        request = self.factory.get('/upload/%s/' % token.uid)
        request.session = SessionDict()
        request.session['_uploads' + token.uid] = token
        response = M2MEdit.as_view()(request, uid=token.uid)
        self.assertIsInstance(response.context_data['creation_form'],
                              forms.ModelForm)
        self.assertIsNone(response.context_data['list_form'])

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_nonempty_token_pks_GET(self):
        files = []
        for i in range(2):
            files.append(file_factory())
        file_pks = [f.pk for f in files]
        str_pks = ','.join([str(pk) for pk in file_pks])
        token = copy.deepcopy(BASE_TOKEN)
        token.pks = file_pks

        request = self.factory.get('/upload/%s/' % token.uid)
        request.session = SessionDict()
        request.session['_uploads' + token.uid] = token
        response = M2MEdit.as_view()(request, uid=token.uid)
        list_form = response.context_data['list_form']
        self.assertIsInstance(list_form, ListForm)
        self.assertEqual(set(list_form.fields['existing_objects'].queryset),
                         set(files))
    
    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_remove_existing_objects_POST(self):
        files = []
        for i in range(2):
            files.append(file_factory())
        file_pks = [f.pk for f in files]
        str_pks = ','.join([str(pk) for pk in file_pks])
        token = copy.deepcopy(BASE_TOKEN)
        token.pks = file_pks

        request = self.factory.post('/upload/%s/' % token.uid,
                {'list-existing_objects': [str(f.pk) for f in files]})
        request.session = SessionDict()
        request.session['_uploads' + token.uid] = token
        response = M2MEdit.as_view()(request, uid=token.uid)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(token.pks, [])

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_create_object_POST(self):
        token = copy.deepcopy(BASE_TOKEN)
        upload = StringIO(b'file_contents')
        upload.name = 'test.txt'
        request = self.factory.post('/upload/%s/' % token.uid,
                {'creation-document': upload}) 
        request.session = SessionDict()
        request.session['_uploads' + token.uid] = token
        response = M2MEdit.as_view()(request, uid=token.uid)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(token.pks), 1)
        file_obj = File.objects.get(pk=token.pks[0])
        self.assertEqual(file_obj.filename, 'test.txt')
    
    def test_GET_no_token(self):
        request = self.factory.get('/upload/%s/' % 'abcde')
        request.session = SessionDict()
        request.session.session_key = '12345'
        response = M2MEdit.as_view()(request, uid='abcde')
        self.assertIn('exception', response.context_data)
        self.assertIsInstance(response.context_data['exception'], TokenError)
    
    def test_POST_no_token(self):
        request = self.factory.post('/upload/%s/' % 'abcde')
        request.session = SessionDict()
        request.session.session_key = '12345'
        response = M2MEdit.as_view()(request, uid='abcde')
        self.assertIn('exception', response.context_data)
        self.assertIsInstance(response.context_data['exception'], TokenError)
