"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.test.utils import override_settings
from django_webtest import WebTest
from webtest import Upload
import shutil
import tempfile
from django.core.files.base import ContentFile
from upload.models import File
from demoapp.models import DemoModel


def filemodel_factory(file_name='foo.txt', content=b'contents'):
#    file = ContentFile(content, name=file_name)
    file = ContentFile(content, name=file_name)
    return File.objects.create(document=file)


def demomodel_factory(n_attachments=1, **kwargs):
    defaults = {"sometext": 'foo'}
    attachments = kwargs.pop('attachments', None)
    defaults.update(**kwargs)
    demo_instance = DemoModel.objects.create(**defaults)
    if not attachments:
        attachments = []
        for i in range(n_attachments):
            attachments.append(
                filemodel_factory(file_name='%s.txt' % i,
                                  content=b'%s_contents' % i,
                                  )
            )
    demo_instance.attachments = attachments
    return demo_instance


class IntegrationTest(WebTest):
    TEMP_MEDIA_ROOT = tempfile.mkdtemp()

    def setUp(self):
        #self.old_media_root = settings.MEDIA_ROOT
        #self.temp_media_root = tempfile.mkdtemp()
        #settings.MEDIA_ROOT = self.temp_media_root
        pass

    def tearDown(self):
        #settings.MEDIA_ROOT = self.old_media_root
        shutil.rmtree(self.TEMP_MEDIA_ROOT)

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
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

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def testUpdate(self):
        """
        Test that we can update a M2M Set
        """
        dm = demomodel_factory(n_attachments=3)
        parent_form = self.app.get('/demoapp/update/%s/' % dm.pk).form
        m2m_link = parent_form.html.find('iframe').attrs['src']
        response = self.app.get(m2m_link)
        # Add one new file
        m2m_form = response.form
        m2m_form['creation-document'] = Upload('NewFile.jpg', b'new_file_data')
        response = m2m_form.submit().follow()
        response = parent_form.submit().follow()
        self.assertEqual(response.status_code, 200)
        context_object = response.context['object']
        files = context_object.attachments.all()
        self.assertEqual(len(files), 4)
