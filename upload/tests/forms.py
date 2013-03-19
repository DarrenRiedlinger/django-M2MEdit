from django import forms
from upload.fields import MultiUploaderField
from upload.models import File


class SimpleRequiredForm(forms.Form):
    attachments = MultiUploaderField(File.objects.all)
