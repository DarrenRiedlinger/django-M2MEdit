from django.db import models
from django.core.files.storage import default_storage
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from upload.fields import MultiUploaderField

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
    
    Should be assigned to a OneToOneField on your source model.
    Implemented as a sepate class (rather than a m2m on the source
    model) to allow saving of the FileSet before the source model instance
    is saved.  This design also allows us to abstract some of the messy parts
    of rendering the FileSet form correctly 
    N.B. A GenericForeignKey implementation was abandoned as it would not
    (directly) support multiple fields linking to FileSet on the same model, ie:
    class Foo(Model):
        attachments = GenericRelation(FileSet)
        final_reports = GenericRelation(FileSet)
    """
    files = models.ManyToManyField(File)
    
    """ 
    OneToOneField Reverse helpers

    The linked_instance property provides a simple method
    of determining which is the correct relationship to follow (since FileSet
    will end up having reverse relationships for every model that points to
    FileSet).
    """       
    @classmethod
    def _get_121s(cls):
        """
        Return all fields that were added to the class as reverses on a
        OneToOne Relation
        """
        one21s = []
        for k,v in cls.__dict__.iteritems():
            if isinstance(v, SingleRelatedObjectDescriptor):
                one21s.append(k)
        return one21s
   
    @property
    def linked_instance(self):
        """
        Return which reverse OneToOne field is used on this instance (a OneToOne 
        field is constrained such that there can only be at most most one valid 
        reverse field per instance).
        """
        # TODO: some form of caching to reduce unecessary queries
        for field in self._get_121s():
            try:
                return(getattr(self, field))
            except ObjectDoesNotExist:
                pass
        return None
    
    def __unicode__(self):
        return 'FileSet-%s' % self.pk

class FileSetField(models.OneToOneField):
    """
    A OneToOneField to FileSet whose fomrclass defaults to a MultiUploaderField
    """

    def formfield(self, **kwargs):
        defaults = {'form_class': MultiUploaderField}
        defaults.update(kwargs)
        return super(FileSetField, self).formfield(**defaults)

