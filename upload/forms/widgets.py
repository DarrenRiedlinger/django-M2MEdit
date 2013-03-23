from django import forms
from django.core.urlresolvers import reverse
from django.forms import CheckboxInput, SelectMultiple
from django.utils.encoding import force_unicode
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe


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

    def format_output(self, rendered_widgets):
        return u'<div class="Multiupload">%s</div>' % u''.join(rendered_widgets)


# Not currently used.
class TableSelectMultiple(SelectMultiple):
    """
    Provides selection of items via checkboxes, with a table row
    being rendered for each item, the first cell in which contains the
    checkbox.

    When providing choices for this field, give the item as the second
    item in all choice tuples. For example, where you might have
    previously used::

        field.choices = [(item.id, item.name) for item in item_list]

    ...you should use::

        field.choices = [(item.id, item) for item in item_list]

    Credit:insin http://djangosnippets.org/snippets/518/
    Adapted item_attrs to take a list of (label, attr) tuples with label rendered
    in the <th> row.
    Adapted __init__ to take an optional label for the checkbox column
    Use conditional_escape instead of escape (allow html item_attrs)
    """
    def __init__(self, item_attrs, checkbox_label='', *args, **kwargs):
        """
        item_attrs
            Defines the attributes of each item which will be displayed
            as a column in each table row, in the order given.

            Any callables in item_attrs will be called with the item to be
            displayed as the sole parameter.

            Any callable attribute names specified will be called and have
            their return value used for display.

            All attribute values will be escaped.
        """
        super(TableSelectMultiple, self).__init__(*args, **kwargs)
        self.item_attrs = item_attrs
        self.checkbox_label = checkbox_label

    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = []
        has_id = attrs and 'id' in attrs
        final_attrs = self.build_attrs(attrs, name=name)
        output = [u'<table class="existing_objects_list">']
        str_values = set([force_unicode(v) for v in value])  # Normalize to strings.
        output.append(u'<tr><th>%s</th>' % conditional_escape(self.checkbox_label))
        for label, attr in self.item_attrs:
            output.append(u'<th>%s</th>' % conditional_escape(label))
        output.append(u'</tr>')
        for i, (option_value, item) in enumerate(self.choices):
            # If an ID attribute was given, add a numeric index as a suffix,
            # so that the checkboxes don't all have the same ID attribute.
            if has_id:
                final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
            cb = CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
            option_value = force_unicode(option_value)
            rendered_cb = cb.render(name, option_value)
            output.append(u'<tr><td>%s</td>' % rendered_cb)
            for label, attr in self.item_attrs:
                if callable(attr):
                    content = attr(item)
                elif callable(getattr(item, attr)):
                    content = getattr(item, attr)()
                else:
                    content = getattr(item, attr)
                output.append(u'<td>%s</td>' % conditional_escape(content))
            output.append(u'</tr>')
        output.append(u'</table>')
        return mark_safe(u'\n'.join(output))
