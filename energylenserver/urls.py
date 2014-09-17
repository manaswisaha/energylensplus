from django.conf.urls import patterns, url
from constants import *

urlpatterns = patterns('energylenserver.views',
                       url(r'^' + UPLOAD_DATA_API, 'upload_data'),
                       url(r'^' + UPLOAD_STATS_API, 'upload_stats'),
                       url(r'^' + REGISTRATION_API, 'register_device'),
                       url(r'^' + TRAINING_API, 'training_data'),
                       url(r'^' + REAL_TIME_POWER_PAST_API, 'real_time_past_data'),
                       url(r'^' + REAL_TIME_POWER_API, 'real_time_data_access'),
                       url(r'^' + REASSIGN_INFERENCE_API, 'reassign_inference'),
                       )
