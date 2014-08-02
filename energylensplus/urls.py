from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
                       # Examples:
                       # url(r'^$', 'energylensplus.views.home', name='home'),
                       # url(r'^blog/', include('blog.urls')),

                       url(r'^admin/', include(admin.site.urls)),
                       url(r'', include('gcm.urls')),
                       )

urlpatterns += patterns('energylenserver.views',
                        url(r'^data/upload/', 'data_upload'),
                        # url(r'^predict', 'predict'),
                        # url(r'^realtime', 'realtime'),
                        # url(r'^final', 'final'),
                        # url(r'^getroomtemperature', 'getroomtemperature'),
                        )
