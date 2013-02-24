from django.db import models
from django.core.files.storage import default_storage
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db.models.fields.related import SingleRelatedObjectDescriptor
from django.core.exceptions import ObjectDoesNotExist
from django.utils.html import escape
from django.utils.safestring import mark_safe


#try:
#    upload_folder = settings.FILE_UPLOAD_FOLDER + '/'
#except AttributeError:
#    upload_folder = 'user_uploads/'
#
#fs = default_storage(storage=fs)
#
# Create your models here.


from sorl.thumbnail import get_thumbnail


#class TempObject(models.Model):
#    """
#    Stores objects which were created using this app, but have not been
#    succesfully saved by the parent form.  Can be used to simplify cleaning up
#    orphaned objects.
#    """
#    uid = models.CharField(max_length=32)
#    last_modified = models.DateTimeField(auto_now_add=True)
#
#    content_type = models.ForeignKey(ContentType)
#    object_id = models.PositiveIntegerField()
#    content_object = generic.GenericForeignKey('content_type', 'object_id')


class File(models.Model):
    # Model for user uploaded files
    filename = models.CharField(max_length=255, editable=False)
    document = models.FileField(upload_to='documents/%Y/%m/%d')
    thumb_url = models.URLField(null=True, blank=True, editable=False)
    upload_date = models.DateTimeField(auto_now_add=True)

    @property
    def url(self):
        return self.document.url

    def __unicode__(self):
        return self.filename

    def __html__(self):
        return mark_safe(u'<a href="%s">%s</a>' % (escape(self.document.url),
                         escape(self.filename)))

    def save(self, *args, **kwargs):
        if not self.pk:
            # Get the uploaded name of the document before our upload handler
            # potentially modifies it
            self.filename = self.document.name
        super(File, self).save(*args, **kwargs)
        try:
            image = get_thumbnail(self.document, "80x80", quality=50)
            self.thumb_url = image.url
        except (IOError, OverflowError):
            # Not recognized as an image by sorl
            pass


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
