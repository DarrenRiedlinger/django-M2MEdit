from django import forms
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.core import validators
from django.utils.datastructures import MultiValueDict, MergeDict
import uuid


class IframeUuidWidget(forms.widgets.HiddenInput):
    """
    Renders a hidden input containing our uuid, and an iframe containing
    the upload view corresponding to that uuid
    """
    def render(self, name, value, attrs=None):
        url = reverse('uid_upload', kwargs={'uid': value},
                      current_app='upload')
        # Can we include div class dynamically
        output = u'<iframe src="%s"></iframe>' % url
        hidden_input = super(IframeUuidWidget, self).render(name,
                                                     value, attrs=attrs)
        return mark_safe('\n'.join((output, hidden_input)))


class SelectMultipleTextInput(forms.widgets.HiddenInput):
    """
    A text input widget customized work with a Multiple Choice Field
    (converting between a python list and a comma-separated string).
    """

    def render(self, name, value, attrs=None):
        if value is None: value = []
        value = ','.join([str(v) for v in value])
        return super(SelectMultipleTextInput, self).render(name, value, attrs)

    def value_from_datadict(self, data, files, name):
        data = data.get(name, None)
        if not data:
            data = []
        else:
            data = data.replace(' ', '').split(',')
        return data


class MultiUploaderIframeWidget(forms.widgets.MultiWidget):
    """
    A widget that renders:
        --an iframe with a link to our fileupload form + hidden uuid input
        --a hidden charfield containing a comma-separated list of selected
          files
    """
    def __init__(self, uid, attrs=None):
        widgets = (
            IframeUuidWidget(attrs=attrs),
            SelectMultipleTextInput(attrs=attrs),
        )
        self.uid = uid
        super(MultiUploaderIframeWidget, self).__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return [value[0], value[1]]
        return [None, None]

    def render(self, name, value, attrs=None):
        """ The default render only decompresses non-lists.  However, our m2m
        field itself is a list, but still needs to be decompressed into [uid,
        [pks]].  This is especially important when the form is passed initial
        data (such as {field_name: [1,2,3]}), which the default render method
        would assume was allready decompressed
        """
        if (not isinstance(value, list)):
            value = self.decompress(value)
        # else if its not a 2-item list in which the second item is
        # itself a list
        elif (len(value) != 2) or (not isinstance(value[-1], list)):
            value = [self.uid, value]
        return super(MultiUploaderIframeWidget, self).render(name, value,
                                                             attrs)

    #def format_output(self, rendered_widgets):
    #    return u'<div class="Multiupload">%s</div>' % u''.join(rendered_widgets)


class MultiUploaderField(forms.MultiValueField):
    """
    Contains a charfield with an autogenerated uuid and a
    ModelMultipleChoiceField.
    """
    def __init__(self, queryset=None, initial=None, *args, **kwargs):
        fields = (
            forms.CharField(),
            forms.ModelMultipleChoiceField(queryset=queryset)
        )
        super(MultiUploaderField, self).__init__(fields, initial=initial,
                                                 *args, **kwargs)
        # We need to dynamically instantiate the widget with our uid.  The
        # widget will rely on this uid when the parent form gets passed an
        # initial value only containing the pk_list (by, say, a model form).
        self.widget = MultiUploaderIframeWidget(uid=self.uid)

    def compress(self, data_list):
        """
        Takes data_list of form [uuid, [<pk list>]] and returns just the pk
        list
        """
        if data_list:
            return data_list[1]
        return None

    @property
    def uid(self):
        """
        Generate a uuid and store it on the instance
        """
        if not getattr(self, '_uid', None):
            self._uid = uuid.uuid4().hex
        return self._uid

    @uid.setter
    def uid(self, value):
        self._uid = value

    @property
    def initial(self):
        return self._initial

    @initial.setter
    def initial(self, value):
        """
        Ensure self.initial is of the format: [uid, pk_list]
        (it will typically be passed a python list of pks, and we need to add
        the uuid)
        """
        if value is None:
            self._initial = [self.uid, []]
        elif isinstance(value, (list, tuple)):
            self._initial = [self.uid, value]
