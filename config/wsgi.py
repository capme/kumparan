"""
WSGI config for lazacom3pl project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

import os

is_gunicorn = "gunicorn" in os.environ.get("SERVER_SOFTWARE", "")

if is_gunicorn:
    # Monkey patch before creating app
    import eventlet
    eventlet.monkey_patch()
    import psycogreen.eventlet
    psycogreen.eventlet.patch_psycopg()
    os.environ.setdefault("EVENTLET_MOCKED", "1")
    os.putenv('EVENTLET_MOCKED', '1')

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

application = get_wsgi_application()
