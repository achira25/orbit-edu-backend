"""
WSGI Configuration for Orbit-Edu
==================================
WSGI = Web Server Gateway Interface.

This file is what Railway/gunicorn uses to START your Django app.
When Railway runs the command in your Procfile:
    gunicorn orbit_edu.wsgi:application
...it's looking for the 'application' variable in THIS file.

You never need to edit this file directly.
"""

import os
from django.core.wsgi import get_wsgi_application

# Tell Django where your settings.py lives
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orbit_edu.settings')

# 'application' is the object gunicorn uses to handle web requests
application = get_wsgi_application()
