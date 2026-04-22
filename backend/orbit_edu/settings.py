"""
ORBIT-EDU Django Settings
=========================
This file controls everything about how Django runs:
- Which apps are installed
- Database configuration
- Security keys
- Static file handling
- CORS (so our frontend on GitHub Pages can talk to this backend)
"""

import os
from pathlib import Path
from decouple import config, Csv

# ─── BASE DIRECTORY ──────────────────────────────────────────────────────────
# Build paths inside the project like: BASE_DIR / 'subdir'
# Path(__file__) = this file (settings.py)
# .resolve().parent.parent = go up two levels to the 'backend/' folder
BASE_DIR = Path(__file__).resolve().parent.parent


# ─── SECURITY ────────────────────────────────────────────────────────────────
# SECRET_KEY: A long random string Django uses to sign cookies and tokens.
# We read it from a .env file (so it's never hard-coded in GitHub).
# The second argument is a fallback used ONLY during local development.
SECRET_KEY = config(
    'SECRET_KEY',
    default='django-insecure-orbit-edu-dev-key-change-in-production-xyz123'
)

# DEBUG: True shows detailed error pages. ALWAYS False in production.
# We read this from .env so Railway can set it to False automatically.
DEBUG = config('DEBUG', default=True, cast=bool)

# ALLOWED_HOSTS: Which domain names Django will respond to.
# In production this will be your Railway URL.
# config('ALLOWED_HOSTS', ...) reads a comma-separated list from .env
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1',
    cast=Csv()
)


# ─── INSTALLED APPS ──────────────────────────────────────────────────────────
# Every Django feature/plugin must be listed here.
INSTALLED_APPS = [
    # Django's built-in apps (admin panel, auth, etc.)
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',   # Handles CSS/JS/image files

    # Third-party packages we installed via requirements.txt
    'rest_framework',               # Django REST Framework - builds our API
    'corsheaders',                  # Allows our GitHub Pages frontend to call this API

    # Our own app that we created
    'tracker',                      # The ISS/satellite tracking app
]


# ─── MIDDLEWARE ───────────────────────────────────────────────────────────────
# Middleware = code that runs on EVERY request before it reaches our views.
# Order matters! corsheaders.middleware MUST be at the very top.
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',        # ← MUST be first for CORS to work
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',    # Serves static files efficiently
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ─── URL CONFIGURATION ───────────────────────────────────────────────────────
# Tells Django where to find the main URL routing file.
ROOT_URLCONF = 'orbit_edu.urls'


# ─── TEMPLATES ───────────────────────────────────────────────────────────────
# Django's HTML template engine configuration.
# We don't use Django templates much (our frontend is separate),
# but the admin panel needs this.
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# ─── WSGI ─────────────────────────────────────────────────────────────────────
# WSGI = Web Server Gateway Interface.
# This is the file that gunicorn (our production server) uses to start Django.
WSGI_APPLICATION = 'orbit_edu.wsgi.application'


# ─── DATABASE ─────────────────────────────────────────────────────────────────
# SQLite: A single file database. Perfect for this project.
# The file 'db.sqlite3' will be created in your backend/ folder.
# You can open it in VS Code with the "SQLite Viewer" extension.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# ─── PASSWORD VALIDATION ──────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ─── INTERNATIONALIZATION ─────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'          # Always use UTC for satellite/space data
USE_I18N = True
USE_TZ = True              # Store all times as timezone-aware


# ─── STATIC FILES ─────────────────────────────────────────────────────────────
# Static files = CSS, JS, images that don't change per-request.
# WhiteNoise serves these efficiently in production on Railway.
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # 'collectstatic' puts files here
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# ─── DEFAULT PRIMARY KEY ──────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ─── CORS SETTINGS ────────────────────────────────────────────────────────────
# CORS = Cross-Origin Resource Sharing.
# Without this, browsers BLOCK your frontend (on github.io) from calling
# your backend (on railway.app) because they're on different domains.
#
# CORS_ALLOWED_ORIGINS: List every frontend URL that's allowed to call our API.
# Add your GitHub Pages URL here after deployment.
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:5500',
    cast=Csv()
)

# Also allow all origins during development (set to False in production)
CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL_ORIGINS', default=True, cast=bool)

# Which HTTP methods the frontend is allowed to use
CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'OPTIONS',
]


# ─── REST FRAMEWORK SETTINGS ──────────────────────────────────────────────────
# Global settings for Django REST Framework (DRF).
REST_FRAMEWORK = {
    # Return JSON by default (not HTML browseable API in production)
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    # Allow anyone to read our public space data API (no login needed)
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    # Throttle: Limit API calls to prevent abuse
    # 1000 calls/day for anonymous users, 5000/day for logged-in users
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '1000/day',
        'user': '5000/day',
    }
}


# ─── EXTERNAL API KEYS ────────────────────────────────────────────────────────
# NASA API key - get yours FREE at https://api.nasa.gov
# Put your real key in .env file, never directly here.
NASA_API_KEY = config('NASA_API_KEY', default='DEMO_KEY')

# ISS API base URL (no key needed - it's completely free)
ISS_API_BASE_URL = 'http://api.open-notify.org'

# Open-Meteo / N2YO alternative for more satellite data
CELESTRAK_API_URL = 'https://celestrak.org/SOCRATES/query.php'
