import json

from django.conf import settings
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.core.signing import SignatureExpired, BadSignature
from recordtype import recordtype


class TokenError(PermissionDenied):
    """
    Could be that cookies are disabled, the token has expired, or the user
    is posting without first recieving a validation cookie
    """
    pass


class TokenExpired(TokenError):
    """
    For specific instances when we know the user has the token, but it has expired
    """
    pass

# We can't just store the form class because form classes can be
# dynamically created (by e.g. modelformfactory)
FileSetToken = recordtype('FileSetToken', [
    'uid',           # the uid generated by the field
    'pks',           # pks selected usign M2MEdit
    'original_pks',  # pks when parent form was rendered
    'field_label',
    'form_class',    # string 'module.class'
    'model_class',   # string 'module.class'
])


def make_token(form, field_label):
    """
    Convencience method for constructing a FileSetToken
    """

    field = form.fields[field_label]
    # if a dyanmic initial value dict was passed to the form
    # class (perhaps by a modelform), that will have precedence
    # over the field intial, so will need that pks list
    try:
        pks = form.initial[field_label]
        uid = field.uid
    # No dynamic initial value on form
    except KeyError:
        uid, pks = field.initial

    return FileSetToken(
        uid=uid,
        pks=pks,
        original_pks=pks,
        field_label=field_label,
        form_class='.'.join(
            (form.__module__, form.__class__.__name__)
        ),
        model_class='.'.join(
            (field.queryset.model.__module__, field.queryset.model.__name__)
        ),
    )


class BaseStorage(object):
    """
    Stores/loads fileset auth tokesn from a cookie
    """
    prefix = 'upload_token_'

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(BaseStorage, self).__init__(*args, **kwargs)

    def _get(self, key, *args, **kwargs):
        raise NotImplementedError()

    def _store(self, token, *args, **kwargs):
        raise NotImplementedError()

    def _remove(self, token, *args, **kwargs):
        raise NotImplementedError()


class SessionStorage(BaseStorage):
    prefix = '_uploads'

    def _get(self, key, *args, **kwargs):
        key = ''.join((self.prefix, key))
        token = self.request.session.get(key)
        if not token:
            if not self.request.session.session_key:
                raise TokenError("You must have cookies enabled to submit this "
                                 "form. Please enable cookies, reload this "
                                 "page and try again.")
            else:
                raise TokenExpired("Sorry, your sesion has expired.  Please "
                                   "reload this page and try again.")
        return token

    def _store(self, tokens, *args, **kwargs):
        for token in tokens:
            key = ''.join((self.prefix, token.uid))
            self.request.session[key] = token

    def _remove(self, tokens, *args, **kwargs):
        for token in tokens:
            key = ''.join((self.prefix, token.uid))
            self.request.session.pop(key, None)


class CookieStorage(BaseStorage):
    """
    Stores/loads fileset auth tokesn from a cookie
    """
    def __init__(self, request, *args, **kwargs):
        raise NotImplementedError

    # Seconds of inactivity between request and response
    max_cookie_age = getattr(settings, 'MULTIUPLOADER_SESSION_TIMEOUT', 300)

    # I don't like this, but its the best I could come up with so far.
    # Currently, if we set the cookie to expire at max_cookie age,
    # there's no easy way to tell if the user's cookie expired or if
    # they are trying to access a page directly without first recieving
    # a cookie.  To provide more helpful http 403 messages, you can set
    # MULTIUPLOADER_COOKIE_LIFETIME to None, causing the cookie to
    # expire on browser close.  max_cookie_age will still be verfied
    # when loading the cookie, and this module will try to delete
    # cookies on a succceful POST to the parent model.  However, some
    # browsers are limited to as little as 20 cookies per domain, which
    # could be limiting if the user initates/abandones a number of
    # upload sessions.
    cookie_lifetime = getattr(settings, 'MULTIUPLOADER_COOKIE_LIFETIME',
                              max_cookie_age)

    def _get(self, key, request, max_age=max_cookie_age):
        # Check that cookies are enabled
        if ''.join((self.prefix, 'TEST')) not in request.COOKIES:
            cookies_enabled = False
        else:
            cookies_enabled = True
        if not cookies_enabled:
            raise PermissionDenied(('You must have cookies enabled to access '
                                    'this resource'))
        key = ''.join((self.prefix, key))
        try:
            cookie = request.get_signed_cookie(key, salt=key, max_age=max_age)
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
        except SignatureExpired:
            # propbably shouldn't raise permission denied, but return a session
            # expired page.
            raise PermissionDenied(('Session has expired, please refresh this '
                                    'page and try again'))
        except BadSignature:
            raise SuspiciousOperation('Fileset token with key %s was tampered'
                                       % key)

        return FileSetToken(*json.loads(cookie))

    def _store(self, tokens, response, request):
        # If session framework is installed, use it's test cookie facilities to
        # determine if cookies are enabled.  Otherwise, set our own test cookie
        if ''.join((self.prefix, 'TEST')) not in request.COOKIES:
                response.set_cookie(key=''.join((self.prefix, 'TEST')),
                                    value='worked')

        for token in tokens:
            key = ''.join((self.prefix, token.uid))
            #pythons cookie class requires an ascii key
            if type(key) == unicode:
                key = key.encode('ascii')
            encoded = json.dumps([v for v in token])
            #encoded = json.dumps(token._asdict())
            response.set_signed_cookie(key=key, value=encoded, salt=key,
                                       max_age=self.cookie_lifetime)
    def remove(self, tokens, response):
        for token in tokens:
            key = ''.join((self.prefix, token.uid))
            #pythons cookie class requires an ascii key
            if type(key) == unicode:
                key = key.encode('ascii')
            response.delete_cookie(key)
