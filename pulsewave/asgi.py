"""
ASGI config for pulsewave project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from workspaces.websocket.middleware import JwtAuthMiddlewareStack
from workspaces.websocket import routing
from notification import routing as notification_routing
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pulsewave.settings')


application = ProtocolTypeRouter({
  "http": get_asgi_application(),
  "websocket": JwtAuthMiddlewareStack(
        URLRouter(
            [
                *routing.websocket_urlpatterns,
                *notification_routing.websocket_urlpatterns,
            ]
        )
    ),
})
