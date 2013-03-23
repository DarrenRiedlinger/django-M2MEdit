from django.db import models
from upload.forms import MultiUploaderField
from django.utils.translation import ugettext_lazy as _


class FileSetField(models.ManyToManyField):
    """
    A MantToManyField to FileSet whose fomrclass defaults to a
    MultiUploaderField
    """
    description = _(('Many-to-many relationship to a File with a '
                     'unique related name and a overridden formfield.'))

    def __init__(self, to, **kwargs):

        # Force a reverse unique reverse descriptor (may be needed for
        # cleaning up orphan uploads with a management command)
        if kwargs['related_name'] is None or '+':
            kwargs['related_name'] = "_%(app_label)s_%(class)s_%(name)s_related"
        super(FileSetField, self).__init__(to, **kwargs)
        # models.ManyToManyField sets its own help_text, which we overide
        self.help_text = getattr(kwargs, 'help_text', '')

    def contribute_to_class(self, cls, name):
        if self.rel.related_name:
            self.rel.related_name = self.rel.related_name % {
                'class': cls.__name__.lower(),
                'app_label': cls._meta.app_label.lower(),
                'name': name.lower()
            }
        super(FileSetField, self).contribute_to_class(cls, name)

    def value_from_object(self, obj):
        """
        Gets called by forms.models.model_to_dict (and possibly others)
        to construct a dyanamic initial dict to pass to the form class
        """
        return super(FileSetField, self).value_from_object(obj)

    def formfield(self, **kwargs):
        defaults = {'form_class': MultiUploaderField}
        defaults.update(kwargs)
        return super(FileSetField, self).formfield(**defaults)
# South custom field introspection
try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ['^upload\.modelfields\.FileSetField'])
except ImportError:
    pass
