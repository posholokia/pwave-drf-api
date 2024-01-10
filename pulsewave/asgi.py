"""
ASGI config for pulsewave project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from django.urls import path, re_path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import django_eventstream

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pulsewave.settings')

application = ProtocolTypeRouter({
    'http': URLRouter([
        path('events/', AuthMiddlewareStack(
            URLRouter(django_eventstream.routing.urlpatterns)
        ), {'channels': ['test', ], }),
        path('events/workspace/',
             URLRouter(django_eventstream.routing.urlpatterns)
             , {'channels': ['workspace', ], }),
        path('events/board/',
             URLRouter(django_eventstream.routing.urlpatterns)
             , {'channels': ['boards', 'column', 'task', ], }),
        # , {'format-channels': ['workspace-{ws_id}', ], }),
        re_path(r'', get_asgi_application()),
    ]),
})
