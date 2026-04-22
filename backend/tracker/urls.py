"""
ORBIT-EDU Tracker App URL Routes
==================================
These URLs all live under /api/ (because orbit_edu/urls.py routes /api/ here).

Full URLs your frontend will call:
  GET https://your-app.railway.app/api/health/
  GET https://your-app.railway.app/api/iss/location/
  GET https://your-app.railway.app/api/iss/history/
  GET https://your-app.railway.app/api/iss/history/?limit=100
  GET https://your-app.railway.app/api/apod/
  GET https://your-app.railway.app/api/apod/?date=2024-01-15
  GET https://your-app.railway.app/api/satellites/
  GET https://your-app.railway.app/api/passes/?lat=28.61&lon=77.20
  GET https://your-app.railway.app/api/astronauts/
"""

from django.urls import path
from . import views

# app_name creates a "namespace" so we can refer to URLs as 'tracker:iss-location'
app_name = 'tracker'

urlpatterns = [
    # ── HEALTH CHECK ─────────────────────────────────────────────────────────
    # Simple ping endpoint to verify API is running
    path(
        'health/',
        views.health_check,
        name='health-check'
    ),

    # ── ISS ENDPOINTS ────────────────────────────────────────────────────────

    # Live ISS position (fetched fresh from external API on every call)
    path(
        'iss/location/',
        views.ISSLocationView.as_view(),
        name='iss-location'
    ),

    # Historical ISS positions from our database
    # Optional: ?limit=100 to get more/fewer positions
    path(
        'iss/history/',
        views.ISSHistoryView.as_view(),
        name='iss-history'
    ),

    # ── NASA APOD ENDPOINTS ──────────────────────────────────────────────────

    # Today's Astronomy Picture of the Day (or ?date=YYYY-MM-DD for specific date)
    path(
        'apod/',
        views.APODView.as_view(),
        name='apod'
    ),

    # ── SATELLITE ENDPOINTS ──────────────────────────────────────────────────

    # List of all satellites in our database
    path(
        'satellites/',
        views.SatelliteListView.as_view(),
        name='satellite-list'
    ),

    # ── ISS PASS PREDICTIONS ─────────────────────────────────────────────────

    # Upcoming ISS passes over a given location
    # Required: ?lat=28.61&lon=77.20
    # Optional: ?alt=220&n=5
    path(
        'passes/',
        views.ISSPassesView.as_view(),
        name='iss-passes'
    ),

    # ── ASTRONAUTS ───────────────────────────────────────────────────────────

    # Who is currently in space?
    path(
        'astronauts/',
        views.AstronautsView.as_view(),
        name='astronauts'
    ),
]
