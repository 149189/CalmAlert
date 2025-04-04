# detection/urls.py
from django.urls import path
from .views import (
    AudioUploadView,
    ModelStatusView,
    EmergencyContactsView,
    StreamingEndpoint
)

urlpatterns = [
    # Audio Processing
    path('audio/upload/', AudioUploadView.as_view(), name='audio-upload'),
    path('stream/', StreamingEndpoint.as_view(), name='audio-stream'),
    
    # System Management
    path('status/', ModelStatusView.as_view(), name='model-status'),
    path('emergency-contacts/', EmergencyContactsView.as_view(), name='emergency-contacts'),
    
    # WebSocket endpoints
    path('ws/monitoring/', MonitoringConsumer.as_asgi(), name='monitoring-ws'),
    path('ws/emergency/', EmergencyConsumer.as_asgi(), name='emergency-ws'),
]