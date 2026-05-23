from django.urls import path

from . import push_api, views

app_name = 'chat'

urlpatterns = [
    path('', views.chat, name='chat'),
    path('dm/<int:pk>/', views.open_dm, name='open_dm'),
    path('add_room/', views.add_room, name='add_room'),
    path('upload/', views.upload_image),
    path('translations/', views.get_translations),

    # Push notification API endpoints
    path('api/push/register/', push_api.PushDeviceRegisterView.as_view(), name='push_register'),
    path('api/push/unregister/', push_api.PushDeviceUnregisterView.as_view(), name='push_unregister'),

    # Toggle notifications endpoint
    path('api/toggle-notifications/', views.toggle_notifications, name='toggle_notifications'),

    # Embedded chat widget API
    path('api/room/<int:room_id>/', views.room_data, name='room_data'),

    # Unread count API (used by home page badge refresh)
    path('api/unread-count/', views.unread_count, name='unread_count'),
]
