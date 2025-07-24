# healthcare_app_motihari/config/asgi.py

import os
import django # <--- ADD THIS IMPORT

# --- IMPORTANT: os.environ.setdefault MUST BE CALLED FIRST ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
# --- END IMPORTANT ---

# --- KEY CHANGE: Explicitly set up Django before other imports ---
django.setup() # <--- ADD THIS LINE
# --- END KEY CHANGE ---


# Now, you can import Django-related modules and your consumers
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path

# And now, import your consumer (it's safe now because django.setup() has run)
from chat.consumers import ChatConsumer


# The Django ASGI application is built after settings are configured
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path('ws/chat/<int:appointment_id>/', ChatConsumer.as_asgi()),
        ])
    ),
})