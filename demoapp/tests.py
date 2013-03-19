"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django_webtest import WebTest
from webtest import Upload
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import shutil
import tempfile


class IntegrationTest(WebTest):
    def setUp(self):
        self.old_media_root = settings.MEDIA_ROOT
        self.temp_media_root = tempfile.mkdtemp()
        settings.MEDIA_ROOT = self.temp_media_root

    def tearDown(self):
        settings.MEDIA_ROOT = self.old_media_root
        shutil.rmtree(self.temp_media_root)


    def testCreate(self):
        """
        Test that we can create a M2M Set
        """
        parent_form = self.app.get('/demoapp/create/').form
        m2m_link = parent_form.html.find('iframe').attrs['src']
        response = self.app.get(m2m_link)
        # Create three files
        m2m_form = response.form
        m2m_form['creation-document'] = Upload('TestFile_0.jpg', b'file_0_data')
        m2m_form = m2m_form.submit().follow().form
        m2m_form['creation-document'] = Upload('TestFile_1.jpg', b'file_1_data')
        m2m_form = m2m_form.submit().follow().form
        m2m_form['creation-document'] = Upload('TestFile_2.jpg', b'file_2_data')
        # On third upload, delete TestFile_1.jpg
        m2m_form.set('list-existing_objects', value=True, index=1)
        response = m2m_form.submit().follow()
        parent_form['sometext'] = 'foo'
        response = parent_form.submit().follow()
        self.assertEqual(response.status_code, 200)
        context_object = response.context['object']
        files = context_object.attachments.all()
        self.assertEqual(len(files), 2)
        file_2 = files.get(filename='TestFile_2.jpg')
        file_2.document.open()
        try:
            self.assertEqual(file_2.document.read(), b'file_2_data')
        finally:
            file_2.document.close()
        self.assertRaises(files.model.DoesNotExist, files.get,
                          filename='TestFile_1.jpg')
