"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.conf import settings
from upload.fields import MultiUploaderField
from upload.models import File
from upload.utils import MultiuploadAuthenticator
from upload.storage import TokenError
from .forms import SimpleRequiredForm, DifferentRequiredForm
from .model_factory import file_factory
from django.test.utils import override_settings
from django.core.exceptions import SuspiciousOperation
import tempfile


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
        # Simulate GET so tokens are added to session
        form = SimpleRequiredForm(initial={'attachments': [1,2,3]})
        MultiuploadAuthenticator(self.request, form)
        token = self.request.session.values()[0]

        form = SimpleRequiredForm({'attachments_0': token.uid,
                                   'attachments_1': '2,3,4'})
        # Modify self.request.session token by reference
        token.pks = [2,3,4]
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
        # Simulate GET so tokens are added to session
        form = SimpleRequiredForm(initial={'attachments': '1,2'})
        MultiuploadAuthenticator(self.request, form)
        token = self.request.session.values()[0]

        form = SimpleRequiredForm({'attachments_0': token.uid,
            'attachments_1': '1,2'})
        # Modify self.request.session token by reference
        token.pks = file_pks
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
        # Simulate GET so tokens are added to session
        form = SimpleRequiredForm(initial={'attachments': [1,2,3]})
        MultiuploadAuthenticator(self.request, form)
        token = self.request.session.values()[0]

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
