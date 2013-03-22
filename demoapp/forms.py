from django import forms


class DemoForm(forms.Form):
    sometext = forms.CharField(max_length=30)
