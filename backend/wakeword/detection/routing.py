# detection/routing.py
from django.urls import re_path
from .consumers import MonitoringConsumer, EmergencyConsumer

websocket_urlpatterns = [
    re_path(r'ws/monitoring/$', MonitoringConsumer.as_asgi()),
    re_path(r'ws/emergency/$', EmergencyConsumer.as_asgi()),
]