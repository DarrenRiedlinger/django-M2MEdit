from django.conf import settings
from django.core.signing import SignatureExpired, BadSignature
from django.core.exceptions import PermissionDenied, SuspiciousOperation
import json
from django.core import signing
# Mutable, named tuples
from recordtype import recordtype

# It's tempting to just store the form itself, and
# serialize/deserialize it using form.__class__ and
# form.__class__.__module__ attributes.  However, form classes
# created using, e.g., modelform_factory are created dynamically and
# can not be properly deserialized/imported from the class and module alone
FileSetToken = recordtype('FileSetToken', [
    'field_value',  # Same as stoage key, but included so its signed
    'field_label',
    'field_required',
    'form_class_name',
    'form_module',

    # If required == True, whether to cause a validation error
    # if the FileSet is made empty. Ideally, the parent model would
    # take care of this, but if you are using a cookie for
    # authorizing the FileSet, there is no way to revoke this cookie
    # after the user submits the parent form (meaning the user could
    # continue editing the FileSet until his/her cookie expires.
    # Left as an optionn since enforcing it creates a somewhat
    # degraded UX (user may have been removing the existing files
    # but planning on adding a new one).
    ('enforce_required', False),
    # Parent model sets pk if instance is being updated, FileSet
    # upload view sets pk if parent model instance is being created
    ('fileset_pk', None),
    ('max_filesize', None),
    ('min_filesize', None),
    ('max_files', None),
    ('mimetypes', None),
])


def make_token(form, field_label, hidden_field_value,
               fileset_pk=None, enforce_required=True):
    """
    Convencience method for constructing a FileSetToken
    """

    field = form.fields[field_label]

    return FileSetToken(
        field_value=hidden_field_value,
        field_label=field_label,
        form_class_name=form.__class__.__name__,
        form_module=form.__module__,
        enforce_required=enforce_required,
        fileset_pk=fileset_pk,
        max_filesize=getattr(field, 'max_filesize', None),
        field_required=getattr(field, 'required', True),
        min_filesize=getattr(field, 'min_filesize', None),
        max_files=getattr(field, 'max_files', None),
        mimetypes=getattr(field, 'mimetypes', None),
    )


class BaseStorage(object):
    """
    Stores/loads fileset auth tokesn from a cookie
    """
    def load(self, key, request=None):
        raise NotImplementedError()

    def add(self, token, response=None):
        raise NotImplementedError()


# class TokenEncoder(json.JSONEncoder):
#     def default(self, obj):
#         if not isinstance(obj, FileSetToken):
#             raise TypeError('Encoder must be passed a FileSetToken recordtype')
#         return super(TokenEncoder, self).default([v for v in obj])
# 
# 
# class TokenDecoder(json.JSONDecoder):
# 
#     def __init__(self):
#         json.JSONDecoder.__init__(self, object_hook=self.list_to_object)
# 
#     def list_to_object(self, l):
#         import ipdb; ipdb.set_trace()
#         args = [v for v in l]
#         return FileSetToken(*args)


class CookieStorage(object):
    """
    Stores/loads fileset auth tokesn from a cookie
    """
    prefix = 'upload_token_'
    # Seconds of inactivity between request and response
    max_cookie_age = getattr(settings, 'MULTIUPLOADER_SESSION_TIMEOUT', 300)

    # I don't like this, but its the best I could come up with so far.
    # Currently, if we set the cookie to expire at max_cookie age, there's no
    # easy way to tell if the user's cookie expired or if they are trying to
    # access a page directly without first recieving a cooke.  To provide more
    # helpful http 403 messages, you can set MULTIUPLOADER_COOKIE_LIFETIME to
    # None, causing the cookie to expire on browser close.  max_cookie_age will
    # still be verfied when loading the cookie, and this module will try to
    # delete cookies on a succceful POST to the parent model.  However, some
    # browsers are limited to as little as 20 cookies per domain, which could
    # be limiting if the user initates/abandones a number of upload sessions.
    cookie_lifetime = getattr(settings, 'MULTIUPLOADER_COOKIE_LIFETIME',
                              max_cookie_age)

    def load(self, key, request):

        cookies_enabled = True
        # Check that cookies are enabled
        import ipdb; ipdb.set_trace()
        if getattr(request, 'session', None):
            if not request.session.test_cookie_worked():
                cookies_enabled = False
            else:
                request.session.delete_test_cookie()
        else:
            if ''.join((self.prefix, 'TEST')) not in request.COOKIES:
                cookies_enabled = False
        if not cookies_enabled:
            raise PermissionDenied(('You must have cookies enabled to access '
                                    'this resource'))
        
        key = ''.join((self.prefix, key))
        try:
            cookie = request.COOKIES[key]
            decoded = signing.loads(cookie, salt=key,
                                    max_age=self.max_cookie_age)
        except KeyError:
            # Kind of annoying. With the optional setting
            # MULTIUPLOADER_COOKIE_LIFETIMe, you can set  the cookies to not
            # expire until browser close, and just verify max_age when loading
            # the cookie.  However, some browsers restrict us to 20 cookies per
            # domain, which could be limiting if abandoned upload cookies
            # aren't expiring.
            raise PermissionDenied(('Sorry, either your session has expired '
                'or you do not have permission to acess this resource. Please '
                'refresh this page and try again.'))
        except BadSignature:
            raise SuspiciousOperation('Fileset token with key %s was tampered')
        except SignatureExpired:
            raise PermissionDenied(('Session has expired, please refresh this '
                                    'page and try again'))

        return FileSetToken(*decoded)

    def add(self, tokens, response, request):
        # If session framework is installed, use it's test cookie facilities to
        # determine if cookies are enabled.  Otherwise, set our own test cookie
        import ipdb; ipdb.set_trace()
        if getattr(request, 'session', None):
            if not request.session.test_cookie_worked():
                request.session.set_test_cookie()
        elif ''.join((self.prefix, 'TEST')) not in request.COOKIES:
                response.set_cookie(key=''.join((self.prefix, 'TEST')),
                                    value='worked')

        for token in tokens:
            key = ''.join((self.prefix, token.field_value))
            #pythons cookie class requires an ascii key
            if type(key) == unicode:
                key = key.encode('ascii')
            encoded = signing.dumps([v for v in token], salt=key,
                                    compress=True)
            import ipdb; ipdb.set_trace()
            response.set_cookie(key=key, value=encoded,
                                max_age=self.cookie_lifetime)

    def remove(self, tokens, response):
        for token in tokens:
            response.delete_cookie(''.join((self.prefix, token.field_value)))
