from django.template import RequestContext, loader
from upload.storage import TokenError
from django.http import HttpResponseForbidden


class TokenExceptionMiddleware(object):
    def process_exception(self, request, exception):
        if isinstance(exception, TokenError):
            return HttpResponseForbidden(loader.render_to_string(
                'missing_token.html',
                context_instance=RequestContext(request,
                                                {'exception': exception})
            )
            )
