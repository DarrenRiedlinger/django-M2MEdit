from django import forms
from django.utils.encoding import force_unicode
from django.core.exceptions import ValidationError


class FileChoiceIterator(forms.models.ModelChoiceIterator):
    """
    Makes 'choices' a tuple containing file url and thumb url
    """
    def choice(self, obj):
        return (self.field.prepare_value(obj),
                self.field.label_from_instance(obj),
                obj.url,
                obj.thumb_url)


class ModelMultipleDeleteField(forms.ModelMultipleChoiceField):
    """
    Like ModelMultipleChoiceField, but ignores pk's that (are not/are no
    longer) in the queryset

    Since FileSetForm causes the existing_files field to only include files
    acutally part of the instance's m2m relationship (rather than, say,
    Files.objects.all() ), if a file is deleted from the instance's m2m
    relationship in between the request and response phase (eg by a different
    user editing the same instance), and our user also tries to delete this
    same files m2m relationship, form validation would fail.  But, since files
    are only being selected for deletion from the m2m relationship, we don't
    care and don't need to raise an exception
    """

    def _get_choices(self):
        if hasattr(self, '_choices'):
            return self._choices

        return FileChoiceIterator(self)

    choices = property(_get_choices, forms.ChoiceField._set_choices)

    def clean(self, value):
        if self.required and not value:
            raise ValidationError(self.error_messages['required'])
        elif not self.required and not value:
            return self.queryset.none()
        if not isinstance(value, (list, tuple)):
            raise ValidationError(self.error_messages['list'])
        key = self.to_field_name or 'pk'
        for pk in value:
            try:
                self.queryset.filter(**{key: pk})
            except ValueError:
                # Don't raise, just delete value from list/tuple
                value = [x for x in value if x != pk]
        qs = self.queryset.filter(**{'%s__in' % key: value})
        pks = set([force_unicode(getattr(o, key)) for o in qs])
        for val in value:
            if force_unicode(val) not in pks:
                raise ValidationError(
                    self.error_messages['invalid_choice'] % val
                )
        # Since this overrides the inherited ModelChoiceField.clean
        # we run custom validators here
        self.run_validators(value)
        return qs


class CustomModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    """
    A ModelMultipleChoiceField that optionally uses a model's __html__() method
    to render the choice field's label.
    The model's __html__ method must properly escape user content
    and return a SafeString to avoid further escaping.
    """
    def label_from_instance(self, obj):
        if hasattr(obj, '__html__'):
            return obj.__html__()
        else:
            return super(CustomModelMultipleChoiceField,
                         self).label_from_instance(obj)
