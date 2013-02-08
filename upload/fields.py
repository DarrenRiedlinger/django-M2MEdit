from django import forms
import uuid

class MultiUploaderWidget(forms.widgets.HiddenInput):
    # Not yet implemented
    def render(self, name, value, attrs=None):
        return super(MultiUploaderWidget, self).render(name, value, attrs=attrs) 


class MultiUploaderField(forms.ModelChoiceField):
    """
    A ModelChoiceField in which 'initial' defaults to a unique id
    """
    widget = MultiUploaderWidget 
    @property
    def initial(self):
        if not self._initial:
            self._initial = uuid.uuid4().hex
        return self._initial
    @initial.setter
    def initial(self, value):
        self._initial = value

