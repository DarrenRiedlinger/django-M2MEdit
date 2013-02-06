from django.db import models
from upload.models import FileSetField
from django.core.urlresolvers import reverse
from django.contrib.contenttypes import generic
# Create your models here.

class DemoModel(models.Model):
    sometext = models.CharField(max_length=30)
    attachments = FileSetField('upload.FileSet', blank=True, null=True)

    def get_absolute_url(self):
        return reverse('crud_detail', args=[self.pk])

    def __unicode__(self):
        return u'Sometext:%s Attachments pk:%s' % (self.sometext, self.attachments)


