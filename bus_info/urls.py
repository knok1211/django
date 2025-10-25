from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('api/bus-seat/', views.get_bus_seat_info, name='bus_seat_info'),
    path('api/route-info/', views.get_route_info, name='route_info'),
    path('api/test/', views.test_api_connection, name='test_api'),
    
    # 데이터 수집 관련 API
    path('api/collection/start/', views.start_data_collection, name='start_collection'),
    path('api/collection/stop/', views.stop_data_collection, name='stop_collection'),
    path('api/collection/status/', views.get_collection_status, name='collection_status'),
    path('api/collection/once/', views.collect_data_once, name='collect_once'),
    path('api/collection/latest/', views.get_latest_data, name='latest_data'),
    path('api/collection/download/', views.download_data_file, name='download_data'),
]
