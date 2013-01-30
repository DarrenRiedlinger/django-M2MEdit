from django.db import models
from django.core.files.storage import default_storage
from django.conf import settings

#try:
#    upload_folder = settings.FILE_UPLOAD_FOLDER + '/'
#except AttributeError:
#    upload_folder = 'user_uploads/'
#
#fs = default_storage(storage=fs)
#
# Create your models here.

class FileUpload(models.Model):
    # Model for user uploaded files
    filename = models.CharField(max_length=255)
    uploaded_file = models.FileField(upload_to='documents/%Y/%m/%d')
    upload_date = models.DateTimeField(auto_now_add=True)
    # uid used to group together files uploaded from the same request
    uid = models.CharField(max_length=32)

