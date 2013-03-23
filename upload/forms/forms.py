from django import forms
from upload.forms.models import CustomModelMultipleChoiceField


class ListForm(forms.Form):
    def __init__(self, queryset, *args, **kwargs):
        super(ListForm, self).__init__(*args, **kwargs)
        self.fields['existing_objects'] = CustomModelMultipleChoiceField(
            queryset=queryset,
            widget=forms.CheckboxSelectMultiple,
            required=False
        )
