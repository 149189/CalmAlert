import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import detection.routing  # Import the app’s WebSocket routes

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wakeword.settings")

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(detection.routing.websocket_urlpatterns)
    ),
})
