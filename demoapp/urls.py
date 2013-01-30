from django.conf.urls.defaults import *

urlpatterns = patterns('demoapp.views',
        url('^', 'demo', name='demoapp'),
        )
