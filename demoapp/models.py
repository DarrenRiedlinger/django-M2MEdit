from django.db import models
from upload.models import FileSetField
from django.core.urlresolvers import reverse


class DemoModel(models.Model):
    sometext = models.CharField(max_length=30)
    attachments = FileSetField('upload.FileSet', blank=True, null=True)
    foo = models.ManyToManyField('upload.File')

    def get_absolute_url(self):
        return reverse('crud_detail', args=[self.pk])

    def __unicode__(self):
        return u'Sometext:%s Attachments pk:%s' % (self.sometext,
                                                   self.attachments)
