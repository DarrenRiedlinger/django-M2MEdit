from django.core.files.base import ContentFile
from upload.models import File


def file_factory(file_name='foo.txt', content=b'contents'):
    file = ContentFile(content, name=file_name)
    return File.objects.create(document=file)
