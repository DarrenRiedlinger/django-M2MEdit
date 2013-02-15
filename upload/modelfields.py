from django.db import models
from upload.fields import MultiUploaderField
from django.utils.translation import ugettext_lazy as _


class FileSetField(models.ManyToManyField):
    """
    A MantToManyField to FileSet whose fomrclass defaults to a
    MultiUploaderField
    """
    description = _(('Many-to-many relationship to a File with a '
                     'unique related name and a overridden formfield.'))

    def __init__(self, to, **kwargs):
        if kwargs['related_name'] is None or '+':
            kwargs['related_name'] = "_%(app_label)s_%(class)s_%(name)s_related"
        super(FileSetField, self).__init__(to, **kwargs)

    def contribute_to_class(self, cls, name):
        if self.rel.related_name:
            self.rel.related_name = self.rel.related_name % {
                'class': cls.__name__.lower(),
                'app_label': cls._meta.app_label.lower(),
                'name': name.lower()
            }
        super(FileSetField, self).contribute_to_class(cls, name)

    def formfield(self, **kwargs):
        defaults = {'form_class': MultiUploaderField}
        defaults.update(kwargs)
        return super(FileSetField, self).formfield(**defaults)
# South custom field introspection
try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ['^upload\.models\.FileSetField'])
except ImportError:
    pass
