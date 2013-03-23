from django.core.urlresolvers import reverse
from django.db import models
from upload.models import FileSetField


class DemoModel(models.Model):
    sometext = models.CharField(max_length=30)
    attachments = FileSetField('upload.File', related_name='+')

    def get_absolute_url(self):
        return reverse('crud_detail', args=[self.pk])
