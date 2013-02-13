from django.db import models
from upload.models import FileSet
from django.contrib.contenttypes import generic
# Create your models here.

class DemoModel(models.Model):
    sometext = models.CharField(max_length=30)
    attachments = generic.GenericRelation(FileSet)
