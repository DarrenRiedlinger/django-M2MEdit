from upload.models import File
from django.core.files.base import ContentFile


def file_factory(file_name='foo.txt', content=b'contents'):
    file = ContentFile(content, name=file_name)
    return File.objects.create(document=file)
