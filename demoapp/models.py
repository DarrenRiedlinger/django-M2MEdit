from django.db import models
from upload.models import FileSet
from django.contrib.contenttypes import generic
# Create your models here.

class DemoModel(models.Model):
    sometext = models.CharField(max_length=30)
    attachments = generic.GenericRelation(FileSet)

    def get_absolute_url(self):
        return reverse('crud_detail', args=[self.pk])

    def __unicode__(self):
        return u'Sometext:%s Attachments pk:%s' % (sometext, attachments.pk)


