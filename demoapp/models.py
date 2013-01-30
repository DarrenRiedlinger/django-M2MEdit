from django.db import models
from upload.models import FileUpload
# Create your models here.

class DemoModel(models.Model):
    sometext = models.CharField(max_length=30)
    attachments = models.ManyToManyField(FileUpload)
