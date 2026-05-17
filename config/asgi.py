import os

import socketio
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django_asgi = get_asgi_application()

from config.socketio_server import sio  # noqa: E402

application = socketio.ASGIApp(sio, django_asgi)
