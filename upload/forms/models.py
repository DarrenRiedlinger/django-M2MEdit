from django import forms


class CustomModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    """
    A ModelMultipleChoiceField that optionally uses a model's __html__() method
    to render the choice field's label.
    The model's __html__ method must properly escape user content
    and return a SafeString to avoid further escaping.
    """
    def label_from_instance(self, obj):
        if hasattr(obj, '__html__'):
            return obj.__html__()
        else:
            return super(CustomModelMultipleChoiceField,
                         self).label_from_instance(obj)
