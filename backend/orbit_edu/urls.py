"""
ORBIT-EDU Main URL Configuration
=================================
This file is the "traffic director" of Django.
Every URL request hits this file first, and Django
decides which app should handle it.

URL Pattern:
  /admin/          → Django's built-in admin panel
  /api/            → All our tracker app API endpoints
  /api/iss/        → Live ISS location
  /api/apod/       → NASA Astronomy Picture of the Day
  /api/satellites/ → Saved satellite records
  /api/history/    → Historical ISS path data
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # ── ADMIN PANEL ──────────────────────────────────────────────────────────
    # Visit /admin in your browser to see Django's built-in admin dashboard.
    # You'll create a superuser account to log in (we'll show you how).
    path('admin/', admin.site.urls),

    # ── API ROUTES ───────────────────────────────────────────────────────────
    # Any URL starting with 'api/' gets passed to tracker/urls.py
    # The include() function means: "go look in tracker/urls.py for the rest"
    # Example: /api/iss/location/ → tracker/urls.py handles 'iss/location/'
    path('api/', include('tracker.urls')),
]
