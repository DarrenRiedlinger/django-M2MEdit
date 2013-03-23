from django.db import models
from django.utils.html import escape
from django.utils.safestring import mark_safe


class File(models.Model):
    """
    Model for user uploaded files.
    """
    filename = models.CharField(max_length=255, editable=False)
    document = models.FileField(upload_to='documents/%Y/%m/%d')
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
