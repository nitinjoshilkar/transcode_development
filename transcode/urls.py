from django.urls import path
from . import views as core_views 


urlpatterns = [
    
    path('transcode/add/', core_views.transcode_data),
    path('transcode/job_id/', core_views.transcode_detail),
    path('transcode/details/', core_views.transcode_detail_webapi),
    path('transcode/job/update/', core_views.transcode_job_update),
    path('transcode/update/job/status/',core_views.transcode_job_update_status),
    

]