from django.views.generic.edit import (ProcessFormView, ModelFormMixin,
        CreateView)
from django.views.generic.detail import SingleObjectTemplateResponseMixin
from django.utils.crypto import get_random_string
from upload.models import FileSetField
import copy

class MockObject(object):
    """
    A mock model instance containing the models FileSetField's
    """
    pass

class BaseMUCreateView(ModelFormMixin, ProcessFormView):
    """
    Populate MockObject with the a model's FileSetField's. Takes care
    of providing unique initial data to the form, making it possible to
    link the uninstantiated model instance to the FileSetField that will
    be creted
    """
    def get(self, request, *args, **kwargs): 
        import ipdb; ipdb.set_trace()
        self.object = MockObject()
        self.object._meta = copy.deepcopy(self.model._meta)
        # Since we can't assign to the ._meta.fields property (no setter)
        # we assign to field_name_cache instead
        self.object._meta._field_name_cache = (
                [x for x in self.object._meta.fields if 
                    isinstance(x, FileSetField)]
                )
        for field in self.object._meta.fields:
            # High-entropy unique string (instead of uuid)
            unique_id = get_random_string(length=13)
            unique_id = 42
            setattr(self.object, field.attname, unique_id)
        return super(BaseMUCreateView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        import ipdb; ipdb.set_trace()
        self.object = None
        return super(BaseMUCreateView, self).post(request, *args, **kwargs)

class MUCreateView(SingleObjectTemplateResponseMixin, BaseMUCreateView):
    template_name_suffix = '_form'

