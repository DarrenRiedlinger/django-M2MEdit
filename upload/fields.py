from django import forms
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
import uuid


class MultiUploaderWidget(forms.widgets.HiddenInput):
    # Not yet implemented
    def render(self, name, value, attrs=None):
        import ipdb; ipdb.set_trace()
        url = reverse('edit_fileset', kwargs={'pk': value},
                      current_app='upload')
        output = u'<div><iframe src="%s"></iframe></div>' % url
        hidden_input = super(MultiUploaderWidget, self).render(name,
                                                        value, attrs=attrs)
        return mark_safe('\n'.join((output, hidden_input)))


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
