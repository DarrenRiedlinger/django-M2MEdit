from django.db import models
from django.core.files.storage import default_storage
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

#try:
#    upload_folder = settings.FILE_UPLOAD_FOLDER + '/'
#except AttributeError:
#    upload_folder = 'user_uploads/'
#
#fs = default_storage(storage=fs)
#
# Create your models here.

class File(models.Model):
    # Model for user uploaded files
    filename = models.CharField(max_length=255)
    document = models.FileField(upload_to='documents/%Y/%m/%d')
    thumb_url = models.URLField(null=True, blank=True)
    upload_date = models.DateTimeField(auto_now_add=True)

    @property
    def url(self):
        return self.document.url

    def __unicode__(self):
        return self.filename

class FileSet(models.Model):
    """
    A set of related files linked to a content_type object
    """
    files = models.ManyToManyField(File)
    content_type = models.ForeignKey(ContentType, null=True)
    object_id = models.PositiveIntegerField(null=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')

