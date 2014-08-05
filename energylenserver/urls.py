from django.conf.urls import patterns, url

urlpatterns = patterns('energylenserver.views',
                       url(r'^data/upload/', 'upload_data'),
                       url(r'^device/register/', 'register_device'),
                       # url(r'^predict', 'predict'),
                       # url(r'^realtime', 'realtime'),
                       # url(r'^final', 'final'),
                       # url(r'^getroomtemperature', 'getroomtemperature'),
                       )
