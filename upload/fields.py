from django import forms
from django.utils.crypto import get_random_string

class MultiUploaderWidget(forms.widgets.HiddenInput):

    def render(self, name, value, attrs=None):
        if value is None:
            #N.B. uuid would provide uniqueness but limited entropy
            value = get_random_string(length=32)
        return super(MultiUploaderWidget, self).render(name, value, attrs=attrs) 

# class MultiUploaderWidget(forms.widgets.Select):
# 
#     def render(self, name, value, attrs=None, choices=()):
#         from upload.models import FileSet
#         if value is None:
#             fs = FileSet()
#             fs.save()
#             value = str(fs.pk)
#         return super(MultiUploaderWidget, self).render(name, value, attrs=attrs, choices=choices) 

class MultiUploaderField(forms.ModelChoiceField):
    widget = MultiUploaderWidget 
    def __init__(self, *args, **kwargs):
        #import ipdb; ipdb.set_trace()
        super(MultiUploaderField, self).__init__(*args, **kwargs)

    
    def _get_choices(self):
        #import ipdb; ipdb.set_trace()
        return super(MultiUploaderField, self)._get_choices()

    choices = property(_get_choices, forms.ChoiceField._set_choices)

