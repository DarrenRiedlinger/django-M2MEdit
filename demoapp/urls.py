from django.conf.urls.defaults import *
from demoapp.views import CrudCreateView, CrudDetailView, CrudUpdateView, CrudDeleteView, CrudListView


urlpatterns = patterns('demoapp.views',
        url (
            regex = '^list/$',
            view = CrudListView.as_view(),
            name = 'crud_list'
            ),
        url (
            regex = '^detail/(?P<pk>\d+)/$',
            view = CrudDetailView.as_view(),
            name = 'crud_detail'
            ),
        
        url (
            regex = '^create/$',
            view = CrudCreateView.as_view(),
            name = 'crud_create'
            ),
        
        url (
            regex = '^delete/(?P<pk>\d+)/$',
            view = CrudDeleteView.as_view(),
            name = 'crud_delete'
            ),
        
        url (
            regex = '^update/(?P<pk>\d+)/$',
            view = CrudUpdateView.as_view(),
            name = 'crud_update'
            ),
)

urlpatterns += patterns('demoapp.views',
        url('^.*/$', 'demo', name='demoapp'),
        )
        
