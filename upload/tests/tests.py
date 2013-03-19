"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.conf import settings
from upload.fields import MultiUploaderField
from upload.models import File
from .forms import SimpleRequiredForm

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
