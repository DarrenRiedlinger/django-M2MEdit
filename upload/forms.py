from django import forms
from upload.models import FileSet
from django.core.exceptions import ImproperlyConfigured
from django.utils.encoding import force_unicode
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from itertools import chain
import uuid

class FileUploadForm(forms.Form):
    file_upload = forms.FileField(
            label='Select a file',
            help_text='TODO: Add some help text',
            required=True,
            )

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
    Like ModelMultipleChoiceField, but ignores pk's that (are not/are
    no longer) in the queryset

    Since FileSetForm causes the existing_files field to only include
    files acutally part of the instance's m2m relationship (rather than, say,
    Files.objects.all() ), if a file is deleted from the instance's m2m
    relationship in between the request and response phase (eg by a different
    user editing the same instance), and our user also tries to delete this same
    files m2m relationship, form validation would fail.  But, since files are
    only being selected for deletion from the m2m relationship, we don't care
    and don't need to raise an exception
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
                #raise ValidationError(self.error_messages['invalid_pk_value'] % pk)
                # Don't raise, just delete from avalue list/tuple
                value = [x for x in value if x != pk]
        qs = self.queryset.filter(**{'%s__in' % key: value})
        pks = set([force_unicode(getattr(o, key)) for o in qs])
        for val in value:
            if force_unicode(val) not in pks:
                raise ValidationError(self.error_messages['invalid_choice'] % val)
        # Since this overrides the inherited ModelChoiceField.clean
        # we run custom validators here
        self.run_validators(value)
        return qs

class CheckboxSelectFiles(forms.CheckboxSelectMultiple):
    def render(self, name, value, attrs=None, choices=()):
        import ipdb; ipdb.set_trace()
        if value is None: value = []
        has_id = attrs and 'id' in attrs
        final_attrs = self.build_attrs(attrs, name=name)
        if not self.choices and not choices:
            return mark_safe(u'<ul><li>No files exist</li></ul>')
        output = [u'<table><tr><th colspan="2">File</th><th>Delete</th>']
        # Normalize to strings
        str_values = set([force_unicode(v) for v in value])
        for i, (option_value, option_label, option_url, option_thumb) in\
                enumerate(chain(self.choices, choices)):
            # If an ID attribute was given, add a numeric index as a suffix,
            # so that the checkboxes don't all have the same ID attribute.
            if has_id:
                final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
                label_for = u' for="%s"' % final_attrs['id']
            else:
                label_for = ''

            cb = forms.CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
            option_value = force_unicode(option_value)
            rendered_cb = cb.render(name, option_value)
            option_label = conditional_escape(force_unicode(option_label))
            if option_thumb:
                option_thumb = force_unicode(option_thumb)
                option_thumb = u'<img src="%s" />' % option_thumb
            else:
                option_thumb = u''
            if option_url:
                option_url = force_unicode(option_url)
                option_label=u'<a href="%s" target="_blank">%s</a>' % (option_url, option_label)
            output.append(u'<tr><td>%s</td><td>%s</td><td><label%s>%s </label></td></tr>'\
                    % (option_thumb, option_label, label_for, rendered_cb) )
        output.append(u'</table')
        return mark_safe(u'\n'.join(output))

class FileSetForm(forms.Form):
    def __init__(self, instance=None, *args, **kwargs):
        super(FileSetForm, self).__init__(*args, **kwargs)
        if instance:
            self.fields['current_files'] = ModelMultipleDeleteField(
                        # TODO: Might be able to use a custom model field and then overide
                        # the model field's formfield method to use our custom queryset and
                        # widget
                        queryset=instance.files.all(),
                        required=False,
                        widget=CheckboxSelectFiles,
                        )

    file_upload = forms.FileField(
         label='Add a file',
         help_text='TODO: Add some help text',
         required=False,
         )

    # Existing_files field gets added dynamically since the queryset is
    # not known until runtime
    #
    # existing_files = None

