from django import forms
import uuid

class FileUploadForm(forms.Form):
    file_upload = forms.FileField(
            label='Select a file',
            help_text='TODO: Add some help text',
            required=True,
            )

