from django import forms
from upload.forms import MultiUploaderField
from upload.models import File


class SimpleRequiredForm(forms.Form):
    attachments = MultiUploaderField(File.objects.all())


class DifferentRequiredForm(forms.Form):
    attachments = MultiUploaderField(File.objects.all())
